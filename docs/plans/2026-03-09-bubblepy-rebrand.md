# bubblepy Rebrand Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rename the package from `bubbletea` to `bubblepy` and strip all Go source/tooling that has no Python context.

**Architecture:** Three phases — delete Go artifacts, update Python module naming, update docs/config references. No logic changes; pure rename and cleanup. The `import bubblepy as tea` idiom is preserved throughout.

**Tech Stack:** Python 3.10+, setuptools, pytest

---

### Task 1: Delete root-level Go source files

**Files:**
- Delete: all `*.go` at repo root (21 files)
- Delete: `go.mod`, `go.sum`
- Delete: `.golangci.yml`, `.goreleaser.yml`
- Delete: `Taskfile.yaml` (Go-only lint/test tasks)

**Step 1: Remove Go source**

```bash
cd /home/matt/github/bubblepy
rm *.go go.mod go.sum .golangci.yml .goreleaser.yml Taskfile.yaml
```

**Step 2: Verify only Python + config remain at root**

```bash
ls *.go 2>/dev/null && echo "FAIL: go files remain" || echo "OK"
ls *.py  # should list: commands.py exec.py keys.py log.py messages.py model.py mouse.py renderer.py screen.py setup.py tea.py
```

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove root-level Go source and Go tooling"
```

---

### Task 2: Delete Go tutorials

**Files:**
- Delete: `tutorials/basics/` (Go tutorial, Python equivalent exists at `tutorials/python-basics/`)
- Delete: `tutorials/commands/` (Go tutorial, Python equivalent exists at `tutorials/python-commands/`)
- Delete: `tutorials/go.mod`, `tutorials/go.sum`

**Step 1: Remove Go tutorial dirs and module files**

```bash
cd /home/matt/github/bubblepy
rm -rf tutorials/basics tutorials/commands tutorials/go.mod tutorials/go.sum
```

**Step 2: Verify Python tutorials remain**

```bash
ls tutorials/
# expected: python-basics/  python-commands/
```

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove Go tutorials (Python equivalents retained)"
```

---

### Task 3: Delete Go example subdirectories

**Files:**
- Delete: all subdirectories under `examples/` (48 dirs, all Go)
- Delete: `examples/go.mod`, `examples/go.sum`
- Delete: `examples/README.md` (Go-focused index)
- Keep: `examples/*.py` (the 9 flat Python example files)

**Step 1: Remove all example subdirectories and Go module files**

```bash
cd /home/matt/github/bubblepy/examples
rm -rf altscreen-toggle autocomplete cellbuffer chat composable-views \
       credit-card-form debounce exec eyes file-picker focus-blur fullscreen \
       glamour help http list-default list-fancy list-simple mouse \
       package-manager pager paginator pipe prevent-quit progress-animated \
       progress-download progress-static realtime result send-msg sequence \
       set-window-title simple spinner spinners split-editors stopwatch \
       suspend table table-resize tabs textarea textinput textinputs timer \
       tui-daemon-combo views window-size \
       go.mod go.sum README.md
```

**Step 2: Verify only Python examples remain**

```bash
ls /home/matt/github/bubblepy/examples/
# expected: basics.py  exec.py  form.py  http.py  mouse.py  realtime.py  send_msg.py  simple.py  views.py
```

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove Go example subdirectories, retain Python examples"
```

---

### Task 4: Rename Python module from `bubbletea` to `bubblepy`

This is the core rename. The `[tool.setuptools.package-dir]` maps `"bubbletea" = ""` — meaning the repo root installs as the `bubbletea` package. After this task it installs as `bubblepy`.

**Files:**
- Modify: `pyproject.toml`
- Modify: `setup.py`
- Modify: `__init__.py`

**Step 1: Update pyproject.toml**

In `pyproject.toml` make these changes:

```toml
# [project]
name = "bubblepy"                    # was: charm-bubbletea
description = "A Python TUI framework based on The Elm Architecture — Python port of the Go Bubble Tea library"

# keywords — replace "bubbletea" entry with "bubblepy"
keywords = [
    "tui",
    "terminal",
    "cli",
    "console",
    "elm-architecture",
    "bubblepy",
    "bubbletea",
    "charm",
]

# [project.urls]
Homepage = "https://github.com/tbdtechpro/bubblepy"
Documentation = "https://github.com/tbdtechpro/bubblepy#readme"
Repository = "https://github.com/tbdtechpro/bubblepy"
Issues = "https://github.com/tbdtechpro/bubblepy/issues"
"Original Go Library" = "https://github.com/charmbracelet/bubbletea"

# [tool.setuptools]
packages = ["bubblepy"]              # was: ["bubbletea"]

# [tool.setuptools.package-dir]
"bubblepy" = ""                      # was: "bubbletea" = ""

# [tool.setuptools.package-data]
bubblepy = ["py.typed"]              # was: bubbletea = ["py.typed"]
```

**Step 2: Update setup.py docstring**

In `setup.py`, change the module docstring:
```python
"""Setup file for bubblepy — Python TUI framework."""
```

**Step 3: Update __init__.py docstring**

In `__init__.py`, change the module docstring:
```python
"""
bubblepy - A Python TUI framework based on The Elm Architecture.

Ported from the Go library: https://github.com/charmbracelet/bubbletea
"""
```

**Step 4: Verify package config looks right**

```bash
cd /home/matt/github/bubblepy
python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(d['project']['name'], d['tool']['setuptools']['packages'])"
# expected: bubblepy ['bubblepy']
```

**Step 5: Commit**

```bash
git add pyproject.toml setup.py __init__.py
git commit -m "chore: rename package from bubbletea to bubblepy in build config"
```

---

### Task 5: Update imports in Python source and tests

Every `import bubbletea` and `from bubbletea.X` becomes `import bubblepy` / `from bubblepy.X`. The `as tea` alias is preserved wherever it exists.

**Files affected:**
- `log.py:35` — `import bubbletea as tea`
- `tests/conftest.py:9-10`
- `tests/test_renderer.py:6`
- `tests/test_keys.py:3`
- `tests/test_commands.py:6-7,19,33`
- `tests/test_mouse.py:3`
- `tests/test_screen.py:3-5`
- `tests/test_program.py:9-10`
- `examples/basics.py:14`
- `examples/exec.py:22`
- `examples/form.py:20`
- `examples/http.py:23`
- `examples/mouse.py:18`
- `examples/realtime.py:24`
- `examples/send_msg.py:24`
- `examples/simple.py:18`
- `examples/views.py:21`

**Step 1: Bulk replace with sed**

```bash
cd /home/matt/github/bubblepy
find . -name "*.py" | xargs sed -i 's/import bubbletea as tea/import bubblepy as tea/g'
find . -name "*.py" | xargs sed -i 's/from bubbletea\./from bubblepy./g'
find . -name "*.py" | xargs sed -i 's/import bubbletea$/import bubblepy/g'
```

**Step 2: Verify no `bubbletea` remains in Python files**

```bash
grep -r "bubbletea" --include="*.py" .
# expected: no output
```

**Step 3: Run the test suite to confirm nothing broke**

```bash
cd /home/matt/github/bubblepy
python -m pytest tests/ -v 2>&1 | tail -20
# expected: all tests pass (or same failures as before this task)
```

**Step 4: Commit**

```bash
git add -A
git commit -m "chore: update Python imports from bubbletea to bubblepy"
```

---

### Task 6: Update documentation and markdown references

**Files:**
- Modify: `README.md` — title, repo URLs
- Modify: `CLAUDE.md` — repo name, overview
- Modify: `CHANGELOG.md` — project name references
- Modify: `Contributing.md` — project name, repo URLs
- Modify: `bubbletea-improvements.md` — filename and internal refs
- Modify: `MVP_TASKS.md`, `MVP_TEST_PLAN.md` — project name
- Modify: `ATTRIBUTION.md` — project name
- Modify: `tutorials/python-basics/README.md`, `tutorials/python-commands/README.md` — import examples

**Step 1: Update README.md title and repo links**

Replace the title line:
```markdown
# bubblepy — Python port (experiment)
```

Update the repo URL wherever it appears:
- `https://github.com/tbdtechpro/bubbletea` → `https://github.com/tbdtechpro/bubblepy`

Leave charmbracelet references intact — they correctly credit the original Go library.

**Step 2: Update CLAUDE.md**

Change the header and overview section to say `bubblepy` and reference `tbdtechpro/bubblepy`.

**Step 3: Bulk replace remaining doc references to the fork's own repo URL**

```bash
cd /home/matt/github/bubblepy
# Replace fork repo URL (not charmbracelet URL)
find . -name "*.md" | xargs sed -i 's|tbdtechpro/bubbletea|tbdtechpro/bubblepy|g'
# Replace "bubbletea" project name where it's used as the Python project name
# (careful: leave "Bubble Tea" / "BubbleTea" references to the Go library intact)
find . -name "*.md" | xargs sed -i 's/^# bubbletea/# bubblepy/g'
```

**Step 4: Rename bubbletea-improvements.md**

```bash
git mv bubbletea-improvements.md bubblepy-improvements.md
```

**Step 5: Update tutorials to use new import**

In `tutorials/python-basics/README.md` and `tutorials/python-commands/README.md`, replace any `import bubbletea` with `import bubblepy`.

```bash
find tutorials/ -name "*.md" | xargs sed -i 's/import bubbletea as tea/import bubblepy as tea/g'
find tutorials/ -name "*.md" | xargs sed -i 's/from bubbletea\./from bubblepy./g'
```

**Step 6: Spot-check key files**

```bash
grep -r "bubbletea" --include="*.md" . | grep -v "charmbracelet\|charm.sh\|Bubble Tea\|BubbleTea\|Go Bubble\|Go library\|go library\|original"
# expected: no output (all remaining "bubbletea" refs should be attributing the Go original)
```

**Step 7: Commit**

```bash
git add -A
git commit -m "docs: rename project to bubblepy throughout documentation"
```

---

### Task 7: Final verification

**Step 1: Confirm no Go artifacts remain**

```bash
find /home/matt/github/bubblepy -name "*.go" -o -name "go.mod" -o -name "go.sum" | grep -v ".git"
# expected: no output
```

**Step 2: Confirm package installs correctly under new name**

```bash
cd /home/matt/github/bubblepy
pip install -e . --quiet
python -c "import bubblepy as tea; print(tea.__version__)"
# expected: 0.1.0
```

**Step 3: Run full test suite**

```bash
python -m pytest tests/ -v
```

**Step 4: Confirm no stray `bubbletea` module references (excluding credited Go library mentions)**

```bash
grep -r "bubbletea" . --include="*.py" --include="*.toml" --include="*.cfg"
# expected: no output
```
