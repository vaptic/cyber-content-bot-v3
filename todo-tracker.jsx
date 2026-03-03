import { useState, useEffect } from "react";

const TODOS = [
  {
    section: "GitHub Repo",
    icon: "⬡",
    color: "#00ff88",
    items: [
      {
        id: "gh1",
        task: "Create a new GitHub repo",
        detail: 'Go to github.com/new → Name it "cyber-content-bot" → Public → No template → Create',
        link: "https://github.com/new",
        linkLabel: "github.com/new",
      },
      {
        id: "gh2",
        task: "Push the project files",
        detail: `Run these commands in your terminal:\n\ngit init\ngit add .\ngit commit -m "🐉 Initial commit: cyber content bot"\ngit remote add origin https://github.com/YOUR_USERNAME/cyber-content-bot.git\ngit branch -M main\ngit push -u origin main`,
        code: true,
      },
      {
        id: "gh3",
        task: "Add ANTHROPIC_API_KEY secret",
        detail: "Repo → Settings → Secrets and variables → Actions → New repository secret\nName: ANTHROPIC_API_KEY\nValue: your key from console.anthropic.com",
        link: "https://console.anthropic.com",
        linkLabel: "Get key at console.anthropic.com",
      },
      {
        id: "gh4",
        task: "Add GOOGLE_API_KEY secret",
        detail: "Same place as above.\nName: GOOGLE_API_KEY\nValue: your free key from aistudio.google.com",
        link: "https://aistudio.google.com",
        linkLabel: "Get key at aistudio.google.com",
      },
      {
        id: "gh5",
        task: "Verify GitHub Actions is enabled",
        detail: "Repo → Settings → Actions → General → Allow all actions → Save",
      },
    ],
  },
  {
    section: "API Keys (Local)",
    icon: "◈",
    color: "#ff6b35",
    items: [
      {
        id: "api1",
        task: "Get Anthropic API key",
        detail: "Go to console.anthropic.com → API Keys → Create Key\nCopy it — you'll need it in the next step.",
        link: "https://console.anthropic.com",
        linkLabel: "console.anthropic.com",
      },
      {
        id: "api2",
        task: "Get Google API key (free)",
        detail: "Go to aistudio.google.com → Get API Key → Create API key\nFree. No billing required. 500 images/day.",
        link: "https://aistudio.google.com",
        linkLabel: "aistudio.google.com",
      },
      {
        id: "api3",
        task: "Add keys to run.py (lines 28–29)",
        detail: `Open run.py and set:\n\nANTHROPIC_API_KEY = "sk-ant-YOUR_KEY_HERE"\nGOOGLE_API_KEY    = "AIza_YOUR_KEY_HERE"`,
        code: true,
      },
    ],
  },
  {
    section: "Local Test Run",
    icon: "▸",
    color: "#a78bfa",
    items: [
      {
        id: "local1",
        task: "Install dependencies",
        detail: `pip install -r requirements.txt`,
        code: true,
      },
      {
        id: "local2",
        task: "Run test (3 images only)",
        detail: `python run.py --test\n\nExpected output:\n  [1/3] Image 01: Identity & Brand...\n  ✓ Saved → image_01_Identity_Brand.png`,
        code: true,
      },
      {
        id: "local3",
        task: "Confirm images appear in output/images/",
        detail: "After test run, check the output/images/ folder.\nYou should see a dated subfolder with 3 PNG files and a manifest.json.",
      },
      {
        id: "local4",
        task: "Run full DragonForce series",
        detail: `python run.py\n\n20 images, ~12 minutes, ~$0.05 total cost.`,
        code: true,
      },
    ],
  },
  {
    section: "GitHub Actions",
    icon: "⟳",
    color: "#38bdf8",
    items: [
      {
        id: "ci1",
        task: "Trigger a manual test run",
        detail: "In your GitHub repo:\nActions → Generate Cybersecurity Images → Run workflow\n→ topic: dragonforce | test_mode: true → Run\n\nShould complete in ~5 minutes.",
      },
      {
        id: "ci2",
        task: "Confirm images committed to repo",
        detail: "After the workflow completes:\nCheck your repo's output/images/ folder.\nYou should see the new images committed by github-actions[bot].",
      },
      {
        id: "ci3",
        task: "Check the schedule is correct",
        detail: "The workflow runs automatically:\n• Monday 07:00 UTC → DragonForce series\n• Wednesday 07:00 UTC → Phishing series\n• Friday 07:00 UTC → Ransomware series\n\nAdjust cron times in .github/workflows/generate.yml if needed.",
      },
    ],
  },
  {
    section: "Content Publishing",
    icon: "◉",
    color: "#fb7185",
    items: [
      {
        id: "pub1",
        task: "Set up LinkedIn native scheduling",
        detail: "LinkedIn allows free post scheduling for all accounts.\nAfter images generate, grab the caption from manifest.json in the image folder.\nUpload image + paste caption on LinkedIn → click the clock icon → Schedule.",
      },
      {
        id: "pub2",
        task: "Add more series topics (optional)",
        detail: "Open run.py → find the SERIES dict → copy one of the existing entries and customise.\nEach series needs: title, context, and a topics list with (number, name, aspect_ratio) tuples.",
      },
      {
        id: "pub3",
        task: "Adjust posting schedule (optional)",
        detail: "Edit .github/workflows/generate.yml\nFind the `schedule:` block and change the cron expressions.\nUse crontab.guru to build custom schedules.",
        link: "https://crontab.guru",
        linkLabel: "crontab.guru",
      },
    ],
  },
];

const totalItems = TODOS.flatMap((s) => s.items).length;

export default function TodoTracker() {
  const [checked, setChecked] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("cyber-todos") || "{}");
    } catch {
      return {};
    }
  });
  const [expanded, setExpanded] = useState({});
  const [activeSection, setActiveSection] = useState(null);

  useEffect(() => {
    try {
      localStorage.setItem("cyber-todos", JSON.stringify(checked));
    } catch {}
  }, [checked]);

  const toggle = (id) => setChecked((p) => ({ ...p, [id]: !p[id] }));
  const toggleDetail = (id) => setExpanded((p) => ({ ...p, [id]: !p[id] }));

  const doneCount = Object.values(checked).filter(Boolean).length;
  const pct = Math.round((doneCount / totalItems) * 100);

  const sectionDone = (section) => {
    const ids = section.items.map((i) => i.id);
    return ids.filter((id) => checked[id]).length;
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#09090b",
      fontFamily: "'DM Mono', 'Fira Code', 'Courier New', monospace",
      color: "#e4e4e7",
      padding: "0",
    }}>
      {/* ── Header ── */}
      <div style={{
        borderBottom: "1px solid #1a1a1f",
        padding: "32px 40px 24px",
        background: "linear-gradient(180deg, #0d0d12 0%, #09090b 100%)",
      }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 16 }}>
          <div>
            <div style={{ fontSize: 11, color: "#52525b", letterSpacing: 4, textTransform: "uppercase", marginBottom: 6 }}>
              Project Setup
            </div>
            <h1 style={{ margin: 0, fontSize: 26, fontWeight: 700, color: "#fafafa", letterSpacing: -1 }}>
              🐉 Cyber Content Bot
            </h1>
            <div style={{ marginTop: 6, fontSize: 12, color: "#71717a" }}>
              Claude API → Gemini Nano Banana Pro → GitHub Actions
            </div>
          </div>

          {/* Progress ring */}
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 36, fontWeight: 700, color: pct === 100 ? "#00ff88" : "#fafafa", letterSpacing: -2 }}>
              {pct}<span style={{ fontSize: 18, color: "#52525b" }}>%</span>
            </div>
            <div style={{ fontSize: 11, color: "#52525b" }}>{doneCount} / {totalItems} done</div>
          </div>
        </div>

        {/* Progress bar */}
        <div style={{ marginTop: 20, height: 3, background: "#1a1a1f", borderRadius: 2 }}>
          <div style={{
            height: "100%",
            width: `${pct}%`,
            background: pct === 100
              ? "linear-gradient(90deg, #00ff88, #00d4aa)"
              : "linear-gradient(90deg, #a78bfa, #38bdf8)",
            borderRadius: 2,
            transition: "width 0.5s cubic-bezier(.4,0,.2,1)",
            boxShadow: pct === 100 ? "0 0 12px #00ff8860" : "0 0 12px #a78bfa40",
          }} />
        </div>
      </div>

      {/* ── Sections ── */}
      <div style={{ maxWidth: 780, margin: "0 auto", padding: "24px 24px 80px" }}>
        {TODOS.map((section, si) => {
          const done = sectionDone(section);
          const total = section.items.length;
          const allDone = done === total;

          return (
            <div key={si} style={{ marginBottom: 12 }}>
              {/* Section header */}
              <button
                onClick={() => setActiveSection(activeSection === si ? null : si)}
                style={{
                  width: "100%",
                  background: activeSection === si ? "#13131a" : "#0f0f14",
                  border: `1px solid ${activeSection === si ? section.color + "40" : "#1a1a1f"}`,
                  borderRadius: activeSection === si ? "10px 10px 0 0" : 10,
                  padding: "14px 18px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  transition: "all 0.2s",
                }}
              >
                <span style={{ fontSize: 18, color: section.color }}>{section.icon}</span>
                <span style={{ flex: 1, textAlign: "left", fontSize: 13, fontWeight: 600, color: "#e4e4e7", letterSpacing: 0.5 }}>
                  {section.section}
                </span>
                <span style={{
                  fontSize: 11,
                  color: allDone ? section.color : "#52525b",
                  background: allDone ? section.color + "15" : "#1a1a1f",
                  border: `1px solid ${allDone ? section.color + "40" : "#27272a"}`,
                  borderRadius: 20,
                  padding: "2px 10px",
                  letterSpacing: 1,
                }}>
                  {done}/{total}
                </span>
                <span style={{ color: "#3f3f46", fontSize: 10 }}>
                  {activeSection === si ? "▲" : "▼"}
                </span>
              </button>

              {/* Items */}
              {activeSection === si && (
                <div style={{
                  border: `1px solid ${section.color + "40"}`,
                  borderTop: "none",
                  borderRadius: "0 0 10px 10px",
                  background: "#0b0b10",
                  overflow: "hidden",
                }}>
                  {section.items.map((item, ii) => {
                    const done = checked[item.id];
                    const open = expanded[item.id];

                    return (
                      <div key={item.id} style={{
                        borderBottom: ii < section.items.length - 1 ? "1px solid #1a1a1f" : "none",
                      }}>
                        <div style={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 14,
                          padding: "14px 18px",
                          background: done ? "#0f1a14" : "transparent",
                          transition: "background 0.2s",
                        }}>
                          {/* Checkbox */}
                          <button
                            onClick={() => toggle(item.id)}
                            style={{
                              width: 20,
                              height: 20,
                              borderRadius: 4,
                              border: `1.5px solid ${done ? section.color : "#3f3f46"}`,
                              background: done ? section.color + "20" : "transparent",
                              cursor: "pointer",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              flexShrink: 0,
                              marginTop: 1,
                              transition: "all 0.15s",
                            }}
                          >
                            {done && <span style={{ color: section.color, fontSize: 12, lineHeight: 1 }}>✓</span>}
                          </button>

                          {/* Content */}
                          <div style={{ flex: 1 }}>
                            <div style={{
                              fontSize: 13,
                              color: done ? "#52525b" : "#e4e4e7",
                              textDecoration: done ? "line-through" : "none",
                              lineHeight: 1.4,
                              textDecorationColor: "#3f3f46",
                            }}>
                              {item.task}
                            </div>
                          </div>

                          {/* Expand button */}
                          <button
                            onClick={() => toggleDetail(item.id)}
                            style={{
                              background: "none",
                              border: "none",
                              color: open ? section.color : "#3f3f46",
                              cursor: "pointer",
                              fontSize: 10,
                              padding: "2px 4px",
                              letterSpacing: 1,
                              flexShrink: 0,
                            }}
                          >
                            {open ? "HIDE" : "HOW"}
                          </button>
                        </div>

                        {/* Detail panel */}
                        {open && (
                          <div style={{
                            padding: "0 18px 16px 52px",
                            background: "#07070c",
                          }}>
                            <pre style={{
                              margin: 0,
                              fontSize: 11.5,
                              color: "#a1a1aa",
                              lineHeight: 1.7,
                              whiteSpace: "pre-wrap",
                              fontFamily: "inherit",
                              background: item.code ? "#0f0f14" : "transparent",
                              border: item.code ? "1px solid #1a1a1f" : "none",
                              borderRadius: item.code ? 6 : 0,
                              padding: item.code ? "10px 14px" : 0,
                              color: item.code ? "#00ff88" : "#a1a1aa",
                            }}>
                              {item.detail}
                            </pre>
                            {item.link && (
                              <a
                                href={item.link}
                                target="_blank"
                                rel="noreferrer"
                                style={{
                                  display: "inline-block",
                                  marginTop: 8,
                                  fontSize: 11,
                                  color: section.color,
                                  textDecoration: "none",
                                  borderBottom: `1px solid ${section.color}40`,
                                }}
                              >
                                ↗ {item.linkLabel}
                              </a>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}

        {/* Done banner */}
        {pct === 100 && (
          <div style={{
            marginTop: 24,
            padding: "20px 24px",
            background: "#00ff8810",
            border: "1px solid #00ff8840",
            borderRadius: 10,
            textAlign: "center",
          }}>
            <div style={{ fontSize: 28 }}>🐉</div>
            <div style={{ marginTop: 8, fontSize: 14, color: "#00ff88", fontWeight: 600 }}>
              Fully operational. Content generating automatically.
            </div>
            <div style={{ marginTop: 4, fontSize: 11, color: "#52525b" }}>
              Mon / Wed / Fri — images commit to your repo while you sleep.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
