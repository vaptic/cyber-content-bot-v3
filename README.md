# 🐉 Cybersecurity Content Bot

Automated cybersecurity image series generator.  
**Claude API** generates cinematic prompts → **Gemini Nano Banana Pro** renders 4K images → **GitHub Actions** commits everything automatically.

## Cost

| Component | Cost |
|-----------|------|
| Claude API (prompts) | ~$0.05 per 20-image series |
| Gemini Nano Banana Pro | $0 (Gemini Advanced subscription) |
| GitHub Actions | $0 (public repo or free tier) |
| **Monthly total** (3 series/week) | **~$0.60** |

---

## Quick Start (local)

```bash
# 1. Clone & install
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
pip install -r requirements.txt

# 2. Add your API keys to run.py (lines 28-29)
#    ANTHROPIC_API_KEY = "sk-ant-..."
#    GOOGLE_API_KEY    = "AIza..."

# 3. Test with 3 images first
python run.py --test

# 4. Full series
python run.py
```

---

## GitHub Actions (fully automated)

Images generate automatically on a schedule and commit back to this repo.

### Schedule
| Day | Series |
|-----|--------|
| Monday | DragonForce Ransomware Cartel (20 images) |
| Wednesday | Anatomy of a Phishing Attack (10 images) |
| Friday | How Ransomware Really Works (10 images) |

### Manual trigger
Go to **Actions → Generate Cybersecurity Images → Run workflow**  
Choose any topic, platform, and image count.

### Setup secrets (one-time)
In your repo: **Settings → Secrets and variables → Actions → New secret**

| Secret name | Value |
|-------------|-------|
| `ANTHROPIC_API_KEY` | Your key from console.anthropic.com |
| `GOOGLE_API_KEY` | Your key from aistudio.google.com |

---

## Available Series

| Topic flag | Series | Images |
|------------|--------|--------|
| `dragonforce` | DragonForce Ransomware Cartel | 20 |
| `phishing` | Anatomy of a Phishing Attack | 10 |
| `zero_trust` | Zero Trust Architecture | 10 |
| `ransomware` | How Ransomware Really Works | 10 |

---

## All Commands

```bash
python run.py                              # Full DragonForce series (default)
python run.py --test                       # Quick test: 3 images only
python run.py --topic phishing             # Different series
python run.py --topic zero_trust
python run.py --platform instagram         # Square 1:1 format
python run.py --platform facebook          # 4:3 format
python run.py --prompts-only               # Claude only, save JSON, skip rendering
python run.py --from-prompts FILE.json     # Skip Claude, render saved prompts
python run.py --start 8                    # Resume from image 8
python run.py --limit 5                    # Generate first 5 images only
python run.py --retry output/.../manifest.json   # Re-render failed images
```

---

## Output Structure

```
output/
  images/
    DRAGONFORCE_RANSOMWARE_CARTEL_20250304_070012/
      image_01_Identity_Brand.png
      image_02_Binary_Signature.png
      ...
      manifest.json          ← captions + hooks ready to copy-paste
  prompts/
    DRAGONFORCE_RANSOMWARE_CARTEL_20250304_070001.json
```

The `manifest.json` in each image folder contains ready-to-post captions and engagement hooks for every image.

---

## Models

- **Prompt generation:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
- **Image rendering:** Gemini Nano Banana Pro (`gemini-3.1-pro-image-preview`)
