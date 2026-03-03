"""
run.py  ─  Claude API (prompts) + Gemini Nano Banana Pro (images)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cost per 20-image series:
  Claude Sonnet 4.6  →  ~$0.05  (prompt generation only)
  Gemini Nano Banana Pro →  $0.00   (included in your Gemini Advanced)
  ─────────────────────────────
  TOTAL              →  ~$0.05 per series

Setup (2 minutes):
  1. pip install anthropic google-genai Pillow
  2. Set ANTHROPIC_API_KEY  → console.anthropic.com  → API Keys
  3. Set GOOGLE_API_KEY     → aistudio.google.com    → Get API Key (FREE)
  4. python run.py

Commands:
  python run.py                          # Full DragonForce 20-image series
  python run.py --test                   # Quick test: 3 images only
  python run.py --topic phishing         # Different series
  python run.py --topic zero_trust       # Zero Trust series
  python run.py --platform instagram     # Instagram 1:1 format
  python run.py --platform facebook      # Facebook 4:3
  python run.py --prompts-only           # Claude only, skip images
  python run.py --from-prompts FILE.json # Use saved prompts, skip Claude
  python run.py --start 8               # Resume from image 8
  python run.py --retry manifest.json   # Re-render failed images
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# ⚙️  CONFIGURATION  — set your two keys here
# ─────────────────────────────────────────────────────────────────────────────

# Keys are read from environment variables (set by GitHub Actions secrets,
# or export them in your shell for local runs):
#   export ANTHROPIC_API_KEY=sk-ant-...
#   export GOOGLE_API_KEY=AIza...
import os as _os
ANTHROPIC_API_KEY = _os.environ.get("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY    = _os.environ.get("GOOGLE_API_KEY", "")

if not ANTHROPIC_API_KEY:
    raise SystemExit("❌ ANTHROPIC_API_KEY not set. Export it or add it to GitHub secrets.")
if not GOOGLE_API_KEY:
    raise SystemExit("❌ GOOGLE_API_KEY not set. Export it or add it to GitHub secrets.")

# Claude model (prompt generation)
CLAUDE_MODEL      = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 8000

# Nano Banana Pro (gemini-3.1-pro-image-preview)
# Included in your Gemini Advanced subscription via API.
# Key upgrades: 4K resolution, near-perfect text-in-image rendering,
#               thinking mode for composition planning.
GEMINI_IMAGE_MODEL = "gemini-3.1-pro-image-preview"

# Nano Banana Pro preview rate limit: ~2 IPM
# 35s gap keeps you safely within the limit.
IMAGE_DELAY_SECONDS = 35

# Output folders
OUT_IMAGES  = "output/images"
OUT_PROMPTS = "output/prompts"

# ─────────────────────────────────────────────────────────────────────────────
# SDK IMPORTS
# ─────────────────────────────────────────────────────────────────────────────

try:
    import anthropic
except ImportError:
    sys.exit("❌ Run: pip install anthropic")

try:
    from google import genai
    from google.genai import types as gtypes
except ImportError:
    sys.exit("❌ Run: pip install google-genai Pillow\n"
             "   (NOT google-generativeai — that package is deprecated)")

os.makedirs(OUT_IMAGES, exist_ok=True)
os.makedirs(OUT_PROMPTS, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# SERIES DATA
# ─────────────────────────────────────────────────────────────────────────────

SERIES = {

    "dragonforce": {
        "title": "DRAGONFORCE RANSOMWARE CARTEL",
        "context": """
DragonForce is a ransomware-as-a-service (RaaS) cartel, publicly emerged December 2023.
KEY FACTS: 363 confirmed victims | 30+ countries | US 52% | UK 12% | AU 6%
212.5% attack surge | Peak: 35 organizations in December 2025
TECHNICAL: BYOVD using truesight.sys + rentdrv2.sys to kill EDR
ENCRYPTION: ChaCha8 cross-platform (Windows, Linux, ESXi)
SOCIAL ENG: Collaborated with Scattered Spider for vishing attacks
VICTIMS: Marks & Spencer, Co-op, Harrods — Summer 2025, £300M+ impact
REVENUE SPLIT: Affiliates keep 80%, cartel takes 20%
KEY DATES: BreachForums debut Dec 6 2023 | Cartel announced Mar 19 2025
           RansomHub absorbed Apr 8 2025
""",
        "topics": [
            ("01", "Identity & Brand — The Circuit Dragon",        "4:5"),
            ("02", "The Binary Signature — Ransom Note Decoded",   "4:5"),
            ("03", "The Origin Nobody Can Confirm",                "4:5"),
            ("04", "Dark Web Emergence — BreachForums Dec 2023",   "4:5"),
            ("05", "The Cartel Announcement — March 19 2025",      "4:5"),
            ("06", "RaaS Franchise — The 80/20 Split",             "4:5"),
            ("07", "363 Victims — 212.5% Surge",                   "4:5"),
            ("08", "Global Reach — 30+ Countries",                 "4:5"),
            ("09", "BYOVD — Your EDR Just Died",                   "4:5"),
            ("10", "Scattered Spider — No Zero-Day Required",      "4:5"),
            ("11", "9 Days Undetected — Lateral Movement",         "4:5"),
            ("12", "Silent Exfiltration — 6TB Stolen",             "4:5"),
            ("13", "Backup Destruction — Last Hope Gone",          "4:5"),
            ("14", "The Encryption Wave — ChaCha8",               "16:9"),
            ("15", "Post-Attack Intimidation — They Call You",     "4:5"),
            ("16", "RansomHub Absorbed — Cartel Grew Overnight",   "4:5"),
            ("17", "UK Retail Assault — £300M Impact",             "4:5"),
            ("18", "Full MITRE Kill Chain — All 10 Steps",         "4:5"),
            ("19", "The 5 Defenses That Stop Them",                "4:5"),
            ("20", "The Dragon Is Already Inside The Walls",      "16:9"),
        ],
    },

    "phishing": {
        "title": "ANATOMY OF A PHISHING ATTACK",
        "context": """
Phishing is the #1 initial access vector — 95% of breaches start here.
The attacker's weapon: a human being who is tired, busy, or trusting.
Key attacks: Spear phishing, vishing, smishing, BEC, MFA fatigue.
Average time from click to credential theft: 82 seconds.
""",
        "topics": [
            ("01", "The Perfect Spear Phish — Anatomy",            "4:5"),
            ("02", "Pretexting — The Story They Told You",         "4:5"),
            ("03", "Urgency Engineering — Why You Clicked",        "4:5"),
            ("04", "The Credential Harvest Page",                  "4:5"),
            ("05", "Business Email Compromise — CEO Fraud",        "4:5"),
            ("06", "Vishing — The Convincing Call",               "4:5"),
            ("07", "Smishing — The Text That Seemed Real",         "4:5"),
            ("08", "MFA Fatigue — The Approval Flood",             "4:5"),
            ("09", "Spot a Phish in 30 Seconds",                   "4:5"),
            ("10", "Phishing-Resistant MFA — Your Last Line",      "4:5"),
        ],
    },

    "zero_trust": {
        "title": "ZERO TRUST ARCHITECTURE",
        "context": """
Zero Trust is not a product — it is a philosophy: Never trust, always verify.
Assume breach at every layer. Verify every user, device, and request.
NIST SP 800-207 defines the framework. CISA provides the maturity model.
Key pillars: Identity, Device, Network, Application, Data.
""",
        "topics": [
            ("01", "The Perimeter Is Dead — Why Firewalls Failed", "4:5"),
            ("02", "Identity Is The New Perimeter",                "4:5"),
            ("03", "Device Trust — Is Your Endpoint Clean",        "4:5"),
            ("04", "Network Micro-Segmentation",                   "4:5"),
            ("05", "Least Privilege — Just Enough Just In Time",   "4:5"),
            ("06", "MFA Everywhere — No Exceptions",               "4:5"),
            ("07", "Continuous Monitoring — Assume Breach Always", "4:5"),
            ("08", "Data Classification — Know What You Protect",  "4:5"),
            ("09", "Zero Trust Maturity Model — 5 Pillars",        "4:5"),
            ("10", "Zero Trust in 90 Days — The Roadmap",         "16:9"),
        ],
    },

    "ransomware": {
        "title": "HOW RANSOMWARE REALLY WORKS",
        "context": """
Modern ransomware attacks unfold silently over 9-21 days before encryption.
The encryption moment is always the LAST step — never the first.
Key stages: Initial access → Lateral movement → Exfiltration → Backup deletion → Encrypt.
Average ransom demand 2025: $2.73M. Average recovery cost: $4.88M.
""",
        "topics": [
            ("01", "The Spear Phish That Started Everything",      "4:5"),
            ("02", "Credential Harvested in 82 Seconds",           "4:5"),
            ("03", "Foothold — Living Off The Land",               "4:5"),
            ("04", "Lateral Movement — Room by Room",              "4:5"),
            ("05", "Silent Exfiltration — Terabytes Gone",         "4:5"),
            ("06", "Backup Destruction — Safety Net Removed",      "4:5"),
            ("07", "Encryption Day — Everything Goes Black",      "16:9"),
            ("08", "The Ransom Note — $2.73M or Goodbye",          "4:5"),
            ("09", "72 Hours on the Clock — The Negotiation",      "4:5"),
            ("10", "What Would Have Stopped It",                   "4:5"),
        ],
    },
}

# Aspect ratio map — Gemini supports: 1:1, 3:4, 4:3, 9:16, 16:9
ASPECT_MAP = {
    "1:1": "1:1", "3:4": "3:4", "4:3": "4:3",
    "9:16": "9:16", "16:9": "16:9",
    "4:5": "3:4",   # 4:5 → use 3:4 (closest supported)
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — CLAUDE API GENERATES PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

CLAUDE_SYSTEM = """You are a world-class AI image prompt engineer specializing in 
cinematic cybersecurity visual storytelling that goes viral on LinkedIn, Instagram, 
and Facebook.

Your signature style:
• TOP STRIP  — title card burned into the image as a designed graphic element
• MAIN VISUAL — hyper-specific, dramatically lit, emotionally charged cinematic scene
• EMBEDDED TEXT — actual text labels burned INTO objects within the scene
  (system error messages, MITRE codes, binary strings, stats, timestamps, company names)
• BOTTOM STRIP — punchy 1-2 line quote or stat burned into the image
• TECH SPECS — exact color palette, lighting direction, photography/art style

Rules:
- All text is a DESIGNED ELEMENT that is part of the artwork, not overlaid after
- Reference real CVEs, real malware names, real MITRE ATT&CK codes where relevant
- Lighting must be cinematic and specific (e.g. "single overhead forensic spotlight",
  "red emergency lighting from below", "volumetric god-rays through storm clouds")
- Output ONLY valid JSON — no markdown fences, no explanation text"""


def generate_prompts(series_key: str, platform: str, limit: int = None) -> tuple[dict, str]:
    """Use Claude API to generate all image prompts for a series."""

    series    = SERIES[series_key]
    title     = series["title"]
    context   = series["context"]
    topics    = series["topics"][:limit] if limit else series["topics"]

    print(f"\n{'═'*62}")
    print(f"  STEP 1 — Claude API generating prompts")
    print(f"  Model  : {CLAUDE_MODEL}")
    print(f"  Series : {title}")
    print(f"  Images : {len(topics)}")
    print(f"  Cost   : ~${len(topics) * 0.0025:.2f} (estimate)")
    print(f"{'═'*62}\n")

    client     = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    all_images = []
    batch_size = 5
    batches    = [topics[i:i+batch_size] for i in range(0, len(topics), batch_size)]

    for b_num, batch in enumerate(batches):
        start_id = int(batch[0][0])
        end_id   = int(batch[-1][0])
        print(f"  Batch {b_num+1}/{len(batches)}  (images {start_id:02d}–{end_id:02d})...")

        topic_block = "\n".join(
            f"  Image {num} — {name}  [aspect: {asp}]"
            for num, name, asp in batch
        )

        user_msg = f"""Generate exactly {len(batch)} cinematic cybersecurity image prompts.

SERIES: "CASE STUDY: {title}"
PLATFORM: {platform}
CONTEXT:
{context}

IMAGES FOR THIS BATCH:
{topic_block}

For EVERY image:
TOP: title card strip "CASE STUDY: {title}" at top of image,
     plus "Topic [num] — [name]" in contrasting font beneath it.
MAIN: richly detailed, dramatically lit scene — specify exact objects,
     people, environments, and what each element represents.
BURNED-IN TEXT: specific real labels on objects within the scene —
     error messages on screens, MITRE codes on walls, binary on glass,
     timestamps in corners, stats on scoreboards. Make them SPECIFIC.
BOTTOM: powerful 1-2 line quote or fact burned across the bottom strip.
SPECS: exact color palette (name specific hex tones), lighting (specific
     direction and mood), photography or art style, aspect ratio.

Return ONLY this JSON object (no markdown, no text before or after):
{{
  "images": [
    {{
      "id": {start_id},
      "topic": "exact topic name",
      "aspect_ratio": "3:4",
      "hook": "one sentence — why this specific image drives engagement",
      "caption": "complete social media caption with 5 hashtags",
      "prompt": "the complete, fully detailed image generation prompt"
    }}
  ]
}}"""

        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                system=CLAUDE_SYSTEM,
                messages=[{"role": "user", "content": user_msg}],
            )

            raw = response.content[0].text.strip()

            # Strip any markdown fences that snuck in
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$",          "", raw).strip()

            data = json.loads(raw)
            imgs = data.get("images", [])

            # Correct IDs and aspect ratios to match our spec
            for i, img in enumerate(imgs):
                img["id"]           = int(batch[i][0])
                img["aspect_ratio"] = ASPECT_MAP.get(batch[i][2], "3:4")

            all_images.extend(imgs)
            usage = response.usage
            print(f"  ✓ {len(imgs)} prompts  |  "
                  f"{usage.input_tokens} in / {usage.output_tokens} out tokens")

        except json.JSONDecodeError as e:
            print(f"  ✗ JSON error in batch {b_num+1}: {e}")
            print(f"    First 400 chars: {raw[:400]}")
        except anthropic.APIError as e:
            print(f"  ✗ Claude API error: {e}")
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")

        if b_num < len(batches) - 1:
            time.sleep(1)   # small pause between Claude calls

    result = {
        "series_title": title,
        "series_key":   series_key,
        "platform":     platform,
        "generated_at": datetime.now().isoformat(),
        "generator":    f"Claude {CLAUDE_MODEL}",
        "total":        len(all_images),
        "images":       all_images,
    }

    # Save to file
    safe  = re.sub(r"[^a-zA-Z0-9_-]", "_", title)[:35]
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    fpath = f"{OUT_PROMPTS}/{safe}_{ts}.json"
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n  ✓ {len(all_images)} prompts saved → {fpath}\n")
    return result, fpath


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — NANO BANANA PRO RENDERS IMAGES
# ─────────────────────────────────────────────────────────────────────────────

def render_images(prompts_data: dict, start_from: int = 1) -> dict:
    """Render all prompts to PNG files using Gemini free image tier."""

    title    = prompts_data["series_title"]
    platform = prompts_data.get("platform", "linkedin")
    images   = [img for img in prompts_data["images"]
                if img.get("id", 0) >= start_from]

    # Create output folder for this run
    safe    = re.sub(r"[^a-zA-Z0-9_-]", "_", title)[:30]
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = f"{OUT_IMAGES}/{safe}_{ts}"
    os.makedirs(out_dir, exist_ok=True)

    est_mins = len(images) * IMAGE_DELAY_SECONDS // 60
    print(f"\n{'═'*62}")
    print(f"  STEP 2 — Nano Banana Pro rendering images")
    print(f"  Model  : {GEMINI_IMAGE_MODEL}")
    print(f"  Images : {len(images)}  (starting from #{start_from:02d})")
    print(f"  Cost   : Included in your Gemini Advanced subscription")
    print(f"  Time   : ~{est_mins} minutes  ({IMAGE_DELAY_SECONDS}s gap per image)")
    print(f"  Output : {out_dir}")
    print(f"{'═'*62}\n")

    gclient = genai.Client(api_key=GOOGLE_API_KEY)
    results = {
        "series_title": title,
        "platform":     platform,
        "model":        GEMINI_IMAGE_MODEL,
        "output_dir":   out_dir,
        "started_at":   datetime.now().isoformat(),
        "results":      [],
    }

    for idx, img in enumerate(images):
        img_id  = img["id"]
        topic   = img.get("topic", f"Image {img_id}")
        prompt  = img.get("prompt", "")
        aspect  = img.get("aspect_ratio", "3:4")
        caption = img.get("caption", "")
        hook    = img.get("hook", "")

        safe_t   = re.sub(r"[^a-zA-Z0-9_-]", "_", topic)[:40]
        filename = f"image_{img_id:02d}_{safe_t}.png"
        filepath = os.path.join(out_dir, filename)

        print(f"  [{idx+1}/{len(images)}] Image {img_id:02d}: {topic}")
        print(f"           Aspect: {aspect} | Prompt: {len(prompt)} chars")

        success = False
        try:
            resp = gclient.models.generate_content(
                model=GEMINI_IMAGE_MODEL,
                contents=prompt,
                config=gtypes.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=gtypes.ImageConfig(aspect_ratio=aspect),
                ),
            )

            for part in resp.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    img_obj = part.as_image()
                    img_obj.save(filepath)
                    print(f"           ✓ Saved → {filename}")
                    success = True
                    break

            if not success:
                # Check if text response hints at a block
                for part in resp.parts:
                    if hasattr(part, "text") and part.text:
                        print(f"           ⚠ Model returned text instead of image: {part.text[:120]}")
                        break
                else:
                    print(f"           ⚠ No image part returned (possible safety filter)")

        except Exception as e:
            print(f"           ✗ Error: {e}")
            # Log for retry
            fail_log = os.path.join(out_dir, "failed.json")
            failed   = json.load(open(fail_log)) if os.path.exists(fail_log) else []
            failed.append({"id": img_id, "topic": topic, "error": str(e)})
            json.dump(failed, open(fail_log, "w"), indent=2)

        results["results"].append({
            "id": img_id, "topic": topic,
            "file": filepath if success else None,
            "caption": caption, "hook": hook, "success": success,
        })

        # Rate limit pause (skip after last image)
        if idx < len(images) - 1:
            print(f"           ⏳ {IMAGE_DELAY_SECONDS}s pause (Nano Banana Pro: ~2 IPM limit)...")
            time.sleep(IMAGE_DELAY_SECONDS)

    # Totals
    ok   = sum(1 for r in results["results"] if r["success"])
    fail = len(images) - ok
    results.update({
        "finished_at": datetime.now().isoformat(),
        "success": ok, "failed": fail,
    })

    # Save manifest
    manifest = os.path.join(out_dir, "manifest.json")
    json.dump(results, open(manifest, "w"), indent=2, ensure_ascii=False)

    elapsed = (datetime.now() - datetime.fromisoformat(results["started_at"])).seconds
    m, s    = divmod(elapsed, 60)

    print(f"\n{'═'*62}")
    print(f"  COMPLETE  |  {ok}/{len(images)} images  |  {m}m {s}s")
    print(f"  Folder  : {out_dir}")
    print(f"  Manifest: {manifest}")
    print(f"{'═'*62}")

    if ok > 0:
        print("\n📋  READY-TO-POST CAPTIONS:")
        print("─" * 62)
        for r in results["results"]:
            if r["success"]:
                print(f"\n[{r['id']:02d}] {r['topic']}")
                print(f"  Hook   : {r['hook']}")
                print(f"  Caption: {r['caption']}")

    if fail > 0:
        print(f"\n⚠  {fail} images failed. Re-run with:")
        print(f"   python run.py --retry {manifest}")

    return results


# ─────────────────────────────────────────────────────────────────────────────
# RETRY FAILED IMAGES
# ─────────────────────────────────────────────────────────────────────────────

def retry_failed(manifest_path: str):
    """Re-render only the images that failed in a previous run."""
    with open(manifest_path) as f:
        prev = json.load(f)

    failed_ids = {r["id"] for r in prev["results"] if not r["success"]}
    if not failed_ids:
        print("✓ No failed images to retry.")
        return

    print(f"  Retrying {len(failed_ids)} failed images: {sorted(failed_ids)}")

    # Find latest prompts file
    prompts_files = sorted(Path(OUT_PROMPTS).glob("*.json"),
                           key=lambda p: p.stat().st_mtime, reverse=True)
    if not prompts_files:
        sys.exit("❌ No prompt files found in output/prompts/")

    with open(prompts_files[0]) as f:
        prompts_data = json.load(f)

    prompts_data["images"] = [
        img for img in prompts_data["images"] if img["id"] in failed_ids
    ]

    render_images(prompts_data)


# ─────────────────────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    valid_topics = list(SERIES.keys())

    ap = argparse.ArgumentParser(
        description="Option 3: Claude API prompts + Gemini FREE images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available series: {', '.join(valid_topics)}

Examples:
  python run.py                            Full DragonForce 20-image series (~$0.05)
  python run.py --test                     Quick test: 3 images only
  python run.py --topic phishing           Phishing awareness series
  python run.py --topic zero_trust         Zero Trust series
  python run.py --platform instagram       Instagram 1:1 format
  python run.py --prompts-only             Claude only, no image rendering
  python run.py --from-prompts FILE.json   Skip Claude, use saved prompts
  python run.py --start 8                  Resume from image 8
  python run.py --retry manifest.json      Re-render only failed images
""")

    ap.add_argument("--topic",        default="dragonforce", choices=valid_topics)
    ap.add_argument("--platform",     default="linkedin",
                    choices=["linkedin","instagram","facebook"])
    ap.add_argument("--test",         action="store_true",
                    help="Test mode: generate first 3 images only")
    ap.add_argument("--prompts-only", action="store_true",
                    help="Generate prompts with Claude, skip image rendering")
    ap.add_argument("--from-prompts", metavar="FILE",
                    help="Skip Claude, use this saved prompts JSON file")
    ap.add_argument("--start",        type=int, default=1,
                    help="Resume from this image number")
    ap.add_argument("--retry",        metavar="MANIFEST",
                    help="Re-render failed images from a previous run's manifest")
    ap.add_argument("--limit",        type=int,
                    help="Generate N images (overrides --test)")

    args = ap.parse_args()

    # ── Retry mode ───────────────────────────────────────────
    if args.retry:
        if not os.path.exists(args.retry):
            sys.exit(f"❌ File not found: {args.retry}")
        retry_failed(args.retry)
        return

    # ── Images-only mode (use saved prompts) ─────────────────
    if args.from_prompts:
        if not os.path.exists(args.from_prompts):
            sys.exit(f"❌ File not found: {args.from_prompts}")
        with open(args.from_prompts) as f:
            prompts_data = json.load(f)
        render_images(prompts_data, start_from=args.start)
        return

    # ── Determine image limit ─────────────────────────────────
    limit = args.limit or (3 if args.test else None)

    # ── Full pipeline: Claude → Gemini ────────────────────────
    prompts_data, prompts_file = generate_prompts(
        series_key=args.topic,
        platform=args.platform,
        limit=limit,
    )

    if args.prompts_only:
        print(f"✓ Prompts-only mode. To render images later:")
        print(f"  python run.py --from-prompts {prompts_file}")
        return

    render_images(prompts_data, start_from=args.start)


if __name__ == "__main__":
    main()
