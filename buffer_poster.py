"""
buffer_poster.py — Step 3 of the pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reads the latest manifest.json and schedules each image + caption
to Buffer via the new GraphQL API (https://api.buffer.com).

Posting schedule (IST = UTC+5:30):
  LinkedIn:  1/day at 12:00pm IST → 06:30 UTC  (starting tomorrow)
  Instagram: 1/day at 12:00pm IST → 06:30 UTC  (starting day after tomorrow)
  Facebook:  1/day at 12:00pm IST → 06:30 UTC  (starting 3 days out)

Images are served as GitHub raw URLs — no file upload needed.

GitHub Secrets required:
  BUFFER_API_KEY        — from publish.buffer.com/settings/api
  LINKEDIN_CHANNEL_ID   — 696db7391214300f602bbdd6
  INSTAGRAM_CHANNEL_ID  — 696db6dd1214300f602bbd5a
  FACEBOOK_CHANNEL_ID   — 696bbf4b457dae6a34192505
  GITHUB_REPO           — vaptic/cyber-content-bot-v3  (set automatically)
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
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

BUFFER_API_KEY        = os.environ.get("BUFFER_API_KEY", "")
GITHUB_REPO           = os.environ.get("GITHUB_REPO", "vaptic/cyber-content-bot-v3")
GITHUB_BRANCH         = "main"

LINKEDIN_CHANNEL_ID   = os.environ.get("LINKEDIN_CHANNEL_ID",  "696db7391214300f602bbdd6")
INSTAGRAM_CHANNEL_ID  = os.environ.get("INSTAGRAM_CHANNEL_ID", "696db6dd1214300f602bbd5a")
FACEBOOK_CHANNEL_ID   = os.environ.get("FACEBOOK_CHANNEL_ID",  "696bbf4b457dae6a34192505")

# 12:00pm IST = 06:30 UTC
POST_HOUR   = 6
POST_MINUTE = 30

BUFFER_GRAPHQL = "https://api.buffer.com"

# ─────────────────────────────────────────────────────────────────────────────
# GRAPHQL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def gql(query: str, variables: dict = None) -> dict:
    """Execute a Buffer GraphQL mutation/query."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    r = requests.post(
        BUFFER_GRAPHQL,
        json=payload,
        headers={
            "Authorization": f"Bearer {BUFFER_API_KEY}",
            "Content-Type":  "application/json",
        },
        timeout=30,
    )
    if not r.ok:
        try:
            err_body = r.json()
        except Exception:
            err_body = r.text
        raise RuntimeError(f"HTTP {r.status_code}: {err_body}")
    data = r.json()

    # Surface GraphQL-level errors
    if "errors" in data:
        raise RuntimeError(f"GraphQL error: {data['errors']}")
    return data


CREATE_POST_MUTATION = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess {
      post {
        id
        text
        dueAt
      }
    }
    ... on MutationError {
      message
    }
  }
}
"""


def schedule_post(channel_id: str, caption: str, image_url: str,
                  due_at: str, dry_run: bool = False) -> dict:
    """
    Schedule one post to Buffer via GraphQL.
    due_at: ISO 8601 UTC string e.g. "2026-03-06T06:30:00Z"
    """
    if dry_run:
        return {"dry_run": True, "channel": channel_id, "due_at": due_at}

    # Append image URL to caption so Buffer generates a preview
    # (full image upload via separate API call is a future enhancement)
    full_text = f"{caption}\n\n{image_url}"

    variables = {
        "input": {
            "channelId":      channel_id,
            "text":           full_text,
            "schedulingType": "automatic",
            "mode":           "customSchedule",
            "dueAt":          due_at,
        }
    }

    result = gql(CREATE_POST_MUTATION, variables)
    payload = result.get("data", {}).get("createPost", {})

    if "message" in payload:
        raise RuntimeError(payload["message"])

    return payload.get("post", {})


# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def github_raw_url(image_path: str) -> str:
    clean = image_path.replace("\\", "/").lstrip("./")
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{clean}"


def schedule_time(base_date: datetime, hour: int = POST_HOUR,
                  minute: int = POST_MINUTE) -> str:
    dt = base_date.replace(hour=hour, minute=minute, second=0,
                           microsecond=0, tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def find_latest_manifest() -> str:
    manifests = sorted(
        Path("output/images").glob("*/manifest.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not manifests:
        sys.exit("❌  No manifest.json found. Run the image generator first.")
    return str(manifests[0])


def check_config():
    if not BUFFER_API_KEY:
        sys.exit("❌  BUFFER_API_KEY not set.")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN POSTER
# ─────────────────────────────────────────────────────────────────────────────

def post_to_buffer(
    manifest_path: str,
    dry_run: bool      = False,
    linkedin: bool     = True,
    instagram: bool    = True,
    facebook: bool     = False,   # opt-in
    limit: int         = None,
):
    check_config()

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    series  = manifest.get("series_title", "Cybersecurity Series")
    results = [r for r in manifest.get("results", []) if r.get("success")]
    if limit:
        results = results[:limit]
    total = len(results)

    if total == 0:
        sys.exit("❌  No successful images in manifest.")

    platforms = []
    if linkedin:  platforms.append(("LinkedIn",  LINKEDIN_CHANNEL_ID))
    if instagram: platforms.append(("Instagram", INSTAGRAM_CHANNEL_ID))
    if facebook:  platforms.append(("Facebook",  FACEBOOK_CHANNEL_ID))

    print(f"\n{'═'*62}")
    print(f"  STEP 3 — Buffer scheduler")
    print(f"  Series   : {series}")
    print(f"  Images   : {total}")
    print(f"  Platforms: {', '.join(p[0] for p in platforms)}")
    print(f"  Schedule : 12:00pm IST daily (06:30 UTC)")
    print(f"  Dry run  : {'YES' if dry_run else 'NO — posting live'}")
    print(f"{'═'*62}\n")

    today    = datetime.now(timezone.utc).replace(
                 hour=0, minute=0, second=0, microsecond=0)

    # Each platform starts on a different day to avoid overlap
    platform_start = {}
    for i, (name, cid) in enumerate(platforms):
        platform_start[name] = today + timedelta(days=1 + i)

    posted = 0
    errors = []

    for idx, item in enumerate(results):
        img_id   = item["id"]
        topic    = item["topic"]
        caption  = item.get("caption", f"#{series.replace(' ', '')}")
        img_file = item.get("file", "")

        if not img_file:
            print(f"  [{idx+1}/{total}] ⚠  Image {img_id:02d} missing file — skipped")
            continue

        raw_url = github_raw_url(img_file)
        print(f"  [{idx+1}/{total}] Image {img_id:02d}: {topic}")

        for name, channel_id in platforms:
            due_at = schedule_time(platform_start[name])
            print(f"           {name:<12} → {due_at}")

            if not dry_run:
                try:
                    schedule_post(channel_id, caption, raw_url,
                                  due_at, dry_run=False)
                    print(f"           {'✓'} Scheduled")
                    posted += 1
                except Exception as e:
                    print(f"           ✗  Error: {e}")
                    errors.append({"id": img_id, "platform": name, "error": str(e)})
            else:
                posted += 1

            # Advance this platform's date by 1 day
            platform_start[name] += timedelta(days=1)

        if not dry_run and idx < total - 1:
            time.sleep(0.3)   # gentle rate limiting

    # ── Summary ───────────────────────────────────────────────
    print(f"\n{'═'*62}")
    if dry_run:
        print(f"  DRY RUN — would schedule {posted} posts across "
              f"{len(platforms)} platform(s)")
        print(f"  First LinkedIn post : {schedule_time(today + timedelta(days=1))}")
        print(f"  Last  LinkedIn post : {schedule_time(today + timedelta(days=total))}")
    else:
        print(f"  ✓ Scheduled {posted} posts")
        if errors:
            print(f"  ✗ {len(errors)} errors:")
            for e in errors:
                print(f"      Image {e['id']} [{e['platform']}]: {e['error']}")
        print(f"\n  📱 Check queue → https://publish.buffer.com")
    print(f"{'═'*62}\n")

    return posted


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Step 3: Auto-schedule generated images to Buffer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python buffer_poster.py --dry-run              # preview without posting
  python buffer_poster.py                        # post LinkedIn + Instagram
  python buffer_poster.py --facebook             # also post to Facebook
  python buffer_poster.py --linkedin-only        # LinkedIn only
  python buffer_poster.py --limit 5              # first 5 images only
  python buffer_poster.py --manifest PATH        # specific manifest
""")
    ap.add_argument("--manifest",       metavar="FILE",
                    help="Path to manifest.json (default: latest)")
    ap.add_argument("--dry-run",        action="store_true",
                    help="Preview schedule without creating posts")
    ap.add_argument("--linkedin-only",  action="store_true")
    ap.add_argument("--instagram-only", action="store_true")
    ap.add_argument("--facebook",       action="store_true",
                    help="Also post to Facebook (off by default)")
    ap.add_argument("--limit",          type=int,
                    help="Only schedule first N images")

    args = ap.parse_args()

    manifest = args.manifest or find_latest_manifest()
    print(f"  Manifest: {manifest}")

    li = not args.instagram_only
    ig = not args.linkedin_only
    fb = args.facebook

    post_to_buffer(
        manifest_path = manifest,
        dry_run       = args.dry_run,
        linkedin      = li,
        instagram     = ig,
        facebook      = fb,
        limit         = args.limit,
    )


if __name__ == "__main__":
    main()
