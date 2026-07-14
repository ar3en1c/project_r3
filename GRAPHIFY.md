# Graphify tutorial — project_r3

**Graphify** turns this repo into a **queryable knowledge graph**: nodes (functions, classes, files) and edges (calls, imports, contains). You ask questions instead of grepping the whole tree.

Official package name on PyPI is **`graphifyy`** (double *y*). The CLI command is still **`graphify`**.

Repo: https://github.com/Graphify-Labs/graphify

---

## What is already set up in this project

| Item | Status |
|------|--------|
| Package | `graphifyy==0.9.15` in `req.txt` / installed in `venv/` |
| Skill (AI assistants) | `.agents/skills/graphify/` (project) + user `~/.agents/skills/graphify/` |
| Ignore rules | `.graphifyignore` (skips venv, large JSON dumps, etc.) |
| First graph | `graphify-out/` — **99 nodes · 64 edges · 42 communities** (code-only) |
| Git hooks | post-commit + post-checkout auto-rebuild on code changes |

### Outputs to open

```
graphify-out/
├── graph.html         ← open in browser (interactive map)
├── GRAPH_REPORT.md    ← god nodes, communities, suggested questions
├── graph.json         ← full graph (query without re-reading code)
└── cache/             ← AST cache (fast re-runs)
```

Open the map:

```powershell
start graphify-out\graph.html
```

---

## 1. Install (new machine / new venv)

```powershell
cd G:\Html\project_r3
.\venv\Scripts\Activate.ps1

# Install package
pip install graphifyy
# or from req.txt:
pip install -r req.txt

# Register skill for AI assistants (project + optional global)
graphify install --project --platform agents
graphify install --platform agents

# Optional: Cursor / Claude / Codex
# graphify cursor install
# graphify install --platform codex
```

**Windows note:** PowerShell treats a leading `/` as a path. Prefer:

```powershell
graphify .
# NOT:  /graphify .
```

If `graphify` is not found:

```powershell
.\venv\Scripts\graphify.exe --version
# or
python -m graphify --version
```

---

## 2. Build the graph

### A) Code only (free, local, no API key) — recommended default

Code is parsed with **tree-sitter AST**. Nothing leaves your machine.

```powershell
graphify extract . --code-only --force
graphify cluster-only . --no-label
```

Or after the first build, refresh when Python/JS changes:

```powershell
graphify update .
```

### B) Code + docs (needs LLM for markdown/docs/images)

Docs like `DOCUMENT.md` need a semantic pass. Either:

1. Run inside an AI assistant: ask it to run the **graphify skill** / type `/graphify .`, or  
2. Headless CLI with an API key:

```powershell
# example backends (pick one you have keys for)
$env:OPENAI_API_KEY = "sk-..."
graphify extract . --backend openai --force

# or Gemini
$env:GEMINI_API_KEY = "..."
graphify extract . --backend gemini --force
```

### C) Rebuild after big refactors

```powershell
graphify extract . --code-only --force
graphify cluster-only .
```

`--force` overwrites even if the new graph has fewer nodes (e.g. you deleted modules).

---

## 3. Query the graph (daily use)

Always from the **project root**, with venv activated (or use full path to the exe).

### Search by question

```powershell
graphify query "how is the series page and footer connected?"
graphify query "Django views and URL routing"
graphify query "rating popover functions" --budget 1500
```

### Explain one symbol

```powershell
graphify explain "footer()"
graphify explain "Series"
graphify explain "_jalali_year()"
```

### Shortest path between two nodes

```powershell
graphify path "footer()" "_jalali_year()"
graphify path "Series" "Genre"
```

### What would break if I change X?

```powershell
graphify affected "footer()"
graphify affected "Series" --depth 3
```

### Real answers from this repo (already run)

**`graphify explain "footer()"`**

```
Node: footer()
  Source:    series/views.py L71
  Community: Community 2
  Degree:    2
Connections:
  <-- views.py [contains] [EXTRACTED]
  --> _jalali_year() [calls] [EXTRACTED]
```

**`graphify query "footer header series views"`** found that:

- `footer()`, `header()`, `series()`, `_jalali_year()` all live under `series/views.py`
- `footer()` → calls → `_jalali_year()` (dynamic Jalali year for copyright)
- Models (`Series`, `Genre`, …) cluster under `series/models.py`
- App URLs: `series/urls.py`; project URLs: `config/urls.py`

Edge confidence tags:

| Tag | Meaning |
|-----|---------|
| **EXTRACTED** | Directly read from code (import, call, class body) |
| **INFERRED** | Resolved by graphify (e.g. cross-file link) |
| **AMBIGUOUS** | Uncertain — treat carefully |

---

## 4. Keep the graph fresh

| Method | When | Cost |
|--------|------|------|
| `graphify update .` | After editing `.py` / `.js` | Free (AST only) |
| Git hooks (`graphify hook install`) | After every commit / checkout | Free |
| `graphify extract . --code-only --force` | Full rebuild | Free |
| `graphify extract .` (with docs + API) | Docs/images changed | API tokens |

Hooks are **already installed** in this repo:

```powershell
graphify hook status
# graphify hook uninstall   # if you want them off
```

---

## 5. Using it with AI (Grok / Cursor / Claude / …)

### Option A — Ask the assistant

With the skill installed, say things like:

- “Use graphify: how does the series footer get its year?”
- “Query the graph for rating UI functions”
- “Path between Series model and series view”

The skill prefers **`graphify query`** over grepping when `graphify-out/graph.json` exists.

### Option B — Skill file

Project skill lives at:

```
.agents/skills/graphify/SKILL.md
```

### Option C — MCP server (optional)

```powershell
pip install "graphifyy[mcp]"
python -m graphify.serve graphify-out/graph.json
```

Gives tools: `query_graph`, `get_node`, `get_neighbors`, `shortest_path`, …

---

## 6. Ignore rules (`.graphifyignore`)

Same syntax as `.gitignore`. This project already skips venv, SQLite, large JSON dumps, font files, etc.

`.gitignore` is respected automatically. `.graphifyignore` only **adds** exclusions.

---

## 7. Workflow cheat sheet

```text
New clone
  → pip install -r req.txt
  → graphify extract . --code-only --force
  → graphify cluster-only .
  → start graphify-out\graph.html

Daily coding
  → edit code
  → commit  (hook rebuilds AST graph)
  → or: graphify update .

Ask architecture questions
  → graphify query "..."
  → graphify explain "Symbol"
  → graphify path "A" "B"
  → read graphify-out\GRAPH_REPORT.md

Include DOCUMENT.md / markdown in the graph
  → set API key + graphify extract . --backend <name>
  → or run full pipeline via AI skill
```

---

## 8. God nodes in *this* project (from last report)

Most connected symbols after the first run:

1. `get_rating_elements()` (JS rating UI)
2. `set_rating()`
3. `_jalali_year()` (footer year helper)
4. `change_rating()` / `toggle_rating_popover()`
5. Models like `Genre`, `RemoteId`, …

Full list: `graphify-out/GRAPH_REPORT.md`

---

## 9. Troubleshooting

| Problem | Fix |
|---------|-----|
| `graphify: command not found` | Use `.\venv\Scripts\graphify.exe` or `python -m graphify` |
| `no LLM API key found` | Add `--code-only`, or set a backend key |
| Graph shrank after refactor | `graphify extract . --code-only --force` |
| Stale after pull | `graphify update .` or re-extract |
| PowerShell `/graphify` error | Use `graphify .` without leading slash |

---

## 10. Uninstall

```powershell
graphify hook uninstall
graphify uninstall                 # remove skills from platforms
# graphify uninstall --purge       # also delete graphify-out/
pip uninstall graphifyy
```
