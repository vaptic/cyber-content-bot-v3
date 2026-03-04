"""
buffer_poster.py — Step 3 of the pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reads manifest.json from the latest image generation run,
then schedules each image + caption to Buffer (LinkedIn + Instagram).

Posting schedule:
  - LinkedIn:  1 post/day at 12:00pm IST (06:30 UTC)
  - Instagram: 1 post/day at 12:30pm IST (07:00 UTC), offset by 1 day
  Images are served from GitHub raw URLs — no upload needed.

Setup:
  1. Add BUFFER_API_KEY to GitHub secrets
  2. Add GITHUB_REPO to GitHub secrets (e.g. "vaptic/cyber-content-bot-v3")
  3. Set LINKEDIN_CHANNEL_ID and INSTAGRAM_CHANNEL_ID below
     (run with --list-channels once to find them)

Usage:
  python buffer_poster.py --list-channels          # find your channel IDs
  python buffer_poster.py --manifest PATH          # post from specific manifest
  python buffer_poster.py                          # post from latest manifest
  python buffer_poster.py --dry-run                # preview without posting
  python buffer_poster.py --linkedin-only          # skip Instagram
  python buffer_poster.py --instagram-only         # skip LinkedIn
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

# ─────────────────────────────────────────────────────────────────────────────
# ⚙️  CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

BUFFER_API_KEY    = os.environ.get("BUFFER_API_KEY", "")
GITHUB_REPO       = os.environ.get("GITHUB_REPO", "vaptic/cyber-content-bot-v3")
GITHUB_BRANCH     = "main"

# ── Paste your channel IDs here after running --list-channels ──
LINKEDIN_CHANNEL_ID  = os.environ.get("LINKEDIN_CHANNEL_ID", "")
INSTAGRAM_CHANNEL_ID = os.environ.get("INSTAGRAM_CHANNEL_ID", "")

# ── Posting times (UTC) ───────────────────────────────────────
# 12:00pm IST = 06:30 UTC  →  LinkedIn
# 12:30pm IST = 07:00 UTC  →  Instagram (30 min offset)
LINKEDIN_POST_HOUR   = 6
LINKEDIN_POST_MINUTE = 30
INSTAGRAM_POST_HOUR  = 7
INSTAGRAM_POST_MINUTE = 0

# Buffer old API base
BUFFER_API_BASE = "https://api.bufferapp.com/1"

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def check_config():
    if not BUFFER_API_KEY:
        sys.exit("❌ BUFFER_API_KEY not set. Add it to GitHub secrets.")
    if not GITHUB_REPO:
        sys.exit("❌ GITHUB_REPO not set (e.g. 'vaptic/cyber-content-bot-v3').")


def buffer_get(endpoint: str) -> dict:
    r = requests.get(
        f"{BUFFER_API_BASE}/{endpoint}",
        headers={"Authorization": f"Bearer {BUFFER_API_KEY}"},
    )
    r.raise_for_status()
    return r.json()


def buffer_post(endpoint: str, data: dict) -> dict:
    r = requests.post(
        f"{BUFFER_API_BASE}/{endpoint}",
        headers={"Authorization": f"Bearer {BUFFER_API_KEY}"},
        data=data,
    )
    r.raise_for_status()
    return r.json()


def github_raw_url(image_path: str) -> str:
    """
    Convert a local output path like:
      output/images/DRAGONFORCE.../image_01_foo.png
    to a GitHub raw URL the Buffer API can fetch.
    """
    # Normalise path separators
    clean = image_path.replace("\\", "/").lstrip("./")
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{clean}"


def schedule_time(base_date: datetime, hour: int, minute: int) -> str:
    """Return ISO 8601 UTC timestamp for a given date at hour:minute UTC."""
    dt = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0,
                           tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def find_latest_manifest() -> str:
    """Find the most recently modified manifest.json under output/images/."""
    manifests = sorted(
        Path("output/images").glob("*/manifest.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not manifests:
        sys.exit("❌ No manifest.json found in output/images/. Run the image generator first.")
    return str(manifests[0])


# ─────────────────────────────────────────────────────────────────────────────
# CHANNEL DISCOVERY
# ─────────────────────────────────────────────────────────────────────────────

def list_channels():
    """Print all Buffer channels — run once to find your IDs."""
    check_config()
    print("\nFetching your Buffer channels...\n")
    try:
        profiles = buffer_get("profiles.json")
    except requests.HTTPError as e:
        sys.exit(f"❌ Buffer API error: {e}")

    print(f"{'ID':<30} {'Service':<15} {'Username'}")
    print("─" * 70)
    for p in profiles:
        svc      = p.get("service", "unknown")
        username = p.get("formatted_username") or p.get("service_username", "")
        pid      = p.get("id", "")
        print(f"{pid:<30} {svc:<15} {username}")

    print("\n📋 Copy the IDs above into your GitHub secrets:")
    print("   LINKEDIN_CHANNEL_ID  = the 'linkedin' row ID")
    print("   INSTAGRAM_CHANNEL_ID = the 'instagram' row ID\n")


# ─────────────────────────────────────────────────────────────────────────────
# POSTING
# ─────────────────────────────────────────────────────────────────────────────

def post_to_buffer(
    manifest_path: str,
    dry_run: bool = False,
    linkedin_only: bool = False,
    instagram_only: bool = False,
    limit: int = None,
):
    check_config()

    if not linkedin_only and not instagram_only:
        if not LINKEDIN_CHANNEL_ID:
            sys.exit("❌ LINKEDIN_CHANNEL_ID not set. Run --list-channels first.")
        if not INSTAGRAM_CHANNEL_ID:
            sys.exit("❌ INSTAGRAM_CHANNEL_ID not set. Run --list-channels first.")
    elif not linkedin_only and not INSTAGRAM_CHANNEL_ID:
        sys.exit("❌ INSTAGRAM_CHANNEL_ID not set.")
    elif not instagram_only and not LINKEDIN_CHANNEL_ID:
        sys.exit("❌ LINKEDIN_CHANNEL_ID not set.")

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    series   = manifest.get("series_title", "Cybersecurity Series")
    results  = [r for r in manifest.get("results", []) if r.get("success")]

    if limit:
        results = results[:limit]

    total = len(results)
    if total == 0:
        sys.exit("❌ No successful images found in manifest.")

    print(f"\n{'═'*62}")
    print(f"  STEP 3 — Buffer auto-poster")
    print(f"  Series  : {series}")
    print(f"  Images  : {total}")
    print(f"  LinkedIn : {'✓' if not instagram_only else '✗'}")
    print(f"  Instagram: {'✓' if not linkedin_only else '✗'}")
    print(f"  Dry run : {'YES — no posts will be created' if dry_run else 'NO — posting live'}")
    print(f"{'═'*62}\n")

    # Start scheduling from tomorrow
    today     = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    li_day    = today + timedelta(days=1)   # LinkedIn starts tomorrow
    ig_day    = today + timedelta(days=2)   # Instagram starts day after (offset)

    li_posted = 0
    ig_posted = 0
    errors    = []

    for idx, item in enumerate(results):
        img_id   = item["id"]
        topic    = item["topic"]
        caption  = item.get("caption", f"#{series.replace(' ','')}")
        img_file = item.get("file", "")

        if not img_file:
            print(f"  [{idx+1}/{total}] ⚠ Image {img_id:02d} has no file path — skipping")
            continue

        raw_url  = github_raw_url(img_file)

        print(f"  [{idx+1}/{total}] Image {img_id:02d}: {topic}")
        print(f"           URL: {raw_url}")

        # ── LinkedIn ──────────────────────────────────────────
        if not instagram_only:
            li_time = schedule_time(li_day, LINKEDIN_POST_HOUR, LINKEDIN_POST_MINUTE)
            print(f"           LinkedIn → {li_time}")

            if not dry_run:
                try:
                    resp = buffer_post("updates/create.json", {
                        "profile_ids[]": LINKEDIN_CHANNEL_ID,
                        "text":          caption,
                        "media[photo]":  raw_url,
                        "scheduled_at":  li_time,
                    })
                    if resp.get("success"):
                        print(f"           ✓ LinkedIn scheduled")
                        li_posted += 1
                    else:
                        print(f"           ✗ LinkedIn error: {resp}")
                        errors.append({"id": img_id, "platform": "linkedin", "error": str(resp)})
                except requests.HTTPError as e:
                    print(f"           ✗ LinkedIn HTTP error: {e}")
                    errors.append({"id": img_id, "platform": "linkedin", "error": str(e)})
            else:
                li_posted += 1

            li_day += timedelta(days=1)

        # ── Instagram ─────────────────────────────────────────
        if not linkedin_only:
            ig_time = schedule_time(ig_day, INSTAGRAM_POST_HOUR, INSTAGRAM_POST_MINUTE)
            print(f"           Instagram → {ig_time}")

            if not dry_run:
                try:
                    resp = buffer_post("updates/create.json", {
                        "profile_ids[]": INSTAGRAM_CHANNEL_ID,
                        "text":          caption,
                        "media[photo]":  raw_url,
                        "scheduled_at":  ig_time,
                    })
                    if resp.get("success"):
                        print(f"           ✓ Instagram scheduled")
                        ig_posted += 1
                    else:
                        print(f"           ✗ Instagram error: {resp}")
                        errors.append({"id": img_id, "platform": "instagram", "error": str(resp)})
                except requests.HTTPError as e:
                    print(f"           ✗ Instagram HTTP error: {e}")
                    errors.append({"id": img_id, "platform": "instagram", "error": str(e)})
            else:
                ig_posted += 1

            ig_day += timedelta(days=1)

        # Small pause between API calls
        if not dry_run and idx < total - 1:
            time.sleep(0.5)

    # ── Summary ───────────────────────────────────────────────
    print(f"\n{'═'*62}")
    if dry_run:
        print(f"  DRY RUN COMPLETE")
        print(f"  Would schedule: {li_posted} LinkedIn + {ig_posted} Instagram posts")
        print(f"  LinkedIn:  {total} posts over {total} days starting tomorrow at 12:00pm IST")
        print(f"  Instagram: {total} posts over {total} days starting in 2 days at 12:30pm IST")
    else:
        print(f"  POSTED: {li_posted} LinkedIn + {ig_posted} Instagram")
        if errors:
            print(f"  ERRORS: {len(errors)}")
            for e in errors:
                print(f"    Image {e['id']} [{e['platform']}]: {e['error']}")
    print(f"{'═'*62}\n")

    if not dry_run:
        print("📱 Check your Buffer queue at: https://publish.buffer.com")

    return li_posted + ig_posted


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Step 3: Post generated images to Buffer (LinkedIn + Instagram)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
First-time setup:
  1. python buffer_poster.py --list-channels
  2. Copy LinkedIn and Instagram IDs into GitHub secrets:
       LINKEDIN_CHANNEL_ID
       INSTAGRAM_CHANNEL_ID
  3. python buffer_poster.py --dry-run   ← preview schedule
  4. python buffer_poster.py             ← go live

Examples:
  python buffer_poster.py --list-channels
  python buffer_poster.py --dry-run
  python buffer_poster.py --manifest output/images/DRAGONFORCE_.../manifest.json
  python buffer_poster.py --linkedin-only
  python buffer_poster.py --limit 5
""")

    ap.add_argument("--list-channels",  action="store_true",
                    help="List all Buffer channels and their IDs")
    ap.add_argument("--manifest",       metavar="FILE",
                    help="Path to manifest.json (default: latest in output/images/)")
    ap.add_argument("--dry-run",        action="store_true",
                    help="Preview schedule without creating posts")
    ap.add_argument("--linkedin-only",  action="store_true")
    ap.add_argument("--instagram-only", action="store_true")
    ap.add_argument("--limit",          type=int,
                    help="Only schedule first N images")

    args = ap.parse_args()

    if args.list_channels:
        list_channels()
        return

    manifest = args.manifest or find_latest_manifest()
    print(f"  Using manifest: {manifest}")

    post_to_buffer(
        manifest_path  = manifest,
        dry_run        = args.dry_run,
        linkedin_only  = args.linkedin_only,
        instagram_only = args.instagram_only,
        limit          = args.limit,
    )


if __name__ == "__main__":
    main()
