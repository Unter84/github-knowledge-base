# SOP: Auto-Updating Folder READMEs on GitHub (Runbook Index)

Use this SOP to set up an automation that **updates folder README files** (and a section in your root README) every time you add or edit a runbook `.md` file.

---

## 🎯 What You’ll Get
- Automatic **index pages** in each folder (e.g., `Firewall/README.md`) listing all runbooks inside.
- An optional **folder index** block inside your root `README.md`.
- Runs automatically via **GitHub Actions** on every push that touches `.md` files.

---

## ✅ Prerequisites
- A GitHub repository (public or private).
- Basic ability to create files in GitHub’s web UI.
- Default branch name (usually `main`).

---

## 📁 Target Folder Structure (example)

SOC-Runbooks/
├─ .github/workflows/update-readmes.yml     # GitHub Actions workflow
├─ scripts/gen_readmes.py                   # Generator script
├─ Firewall/
│  ├─ .md
│  └─ README.md                             # auto-managed
├─ Windows/
│  └─ README.md                             # auto-managed (can be empty at first)
├─ Linux/
│  └─ README.md                             # auto-managed (can be empty at first)
└─ README.md                                # root README (with anchors)

> You can add/remove folders later. The script uses a list called `FOLDERS`.

---

## 🧩 Step 1 — Create the Generator Script

1) In your repo, click **Add file → Create new file**.  
2) Name it **exactly**:

scripts/gen_readmes.py

3) Paste the following:

```python
#!/usr/bin/env python3
import os, re, pathlib, sys
from datetime import datetime

# Edit this list to match your repo folders
FOLDERS = ["Firewall", "Windows", "Linux", "Cloud", "Email", "Endpoint", "Network"]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

def title_from_md(path: pathlib.Path) -> str:
    # Use first Markdown heading as the title; fallback to file name
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.strip().startswith("#"):
                    title = re.sub(r"^#+\s*", "", line).strip()
                    return title
    except Exception:
        pass
    name = path.stem.replace("-", " ").replace("_", " ").strip().title()
    return name

def build_folder_readme(folder: pathlib.Path) -> str:
    files = sorted(
        [p for p in folder.glob("*.md") if p.name.lower() != "readme.md"],
        key=lambda p: p.name.lower(),
    )
    lines = []
    header = f"# 🔥 {folder.name} Runbooks\n\nThis folder contains runbooks related to **{folder.name}** alerts and incidents.\n\n---\n\n## 📘 Available Runbooks\n"
    lines.append(header)

    if not files:
        lines.append("_(No runbooks yet—add some `.md` files!)_\n")
    else:
        for md in files:
            title = title_from_md(md)
            rel = md.name
            lines.append(f"- [{title}]({rel})")

    notes = """
\n---\n
## 🛡️ Usage Notes
- Each runbook follows a standard structure: Detection → Analysis (L1→L2→L3) → Containment → Eradication & Recovery → Evidence → Recommendations → Reporting.
- Cross-reference with SIEM, ticketing, and CMDB during triage.\n
"""
    lines.append(notes)
    footer = f"\n_Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')} (UTC)_\n"
    lines.append(footer)
    return "\n".join(lines).strip() + "\n"

def update_root_readme(root: pathlib.Path):
    # Optional: update a block in the root README between anchors.
    root_readme = root / "README.md"
    if not root_readme.exists():
        return
    links = []
    for name in FOLDERS:
        if (root / name).exists():
            links.append(f"- [{name}]({name}/README.md)")
    if not links:
        return

    with root_readme.open("r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    block_start = "<!-- AUTO-INDEX:START -->"
    block_end   = "<!-- AUTO-INDEX:END -->"
    index_md = "\n".join(links)

    injected = (
        f"{block_start}\n\n## 📂 Runbook Folders\n{index_md}\n\n{block_end}"
    )

    if block_start in content and block_end in content:
        content = re.sub(
            rf"{re.escape(block_start)}.*?{re.escape(block_end)}",
            injected,
            content,
            flags=re.S,
        )
    else:
        content = content.rstrip() + "\n\n" + injected + "\n"

    with root_readme.open("w", encoding="utf-8") as f:
        f.write(content)

def main():
    changed = False
    for name in FOLDERS:
        folder = REPO_ROOT / name
        if not folder.exists():
            continue
        readme_path = folder / "README.md"
        new_md = build_folder_readme(folder)
        old_md = ""
        if readme_path.exists():
            with readme_path.open("r", encoding="utf-8", errors="ignore") as f:
                old_md = f.read()
        if old_md != new_md:
            readme_path.parent.mkdir(parents=True, exist_ok=True)
            with readme_path.open("w", encoding="utf-8") as f:
                f.write(new_md)
            print(f"Updated {readme_path}")
            changed = True

    update_root_readme(REPO_ROOT)
    return 0 if changed else 0

if __name__ == "__main__":
    sys.exit(main())```

	4.	Click Commit new file.

⸻

⚙️ Step 2 — Create the GitHub Actions Workflow
	1.	Add file → Create new file.
	2.	Name it:

.github/workflows/update-readmes.yml

	3.	Paste this:

name: Update folder READMEs

on:
  push:
    branches: [ main, master ]
    paths:
      - "**/*.md"
      - "scripts/gen_readmes.py"
  workflow_dispatch:

permissions:
  contents: write  # allow the workflow to commit changes

jobs:
  build-index:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.x"

      - name: Generate folder READMEs
        run: |
          python scripts/gen_readmes.py

      - name: Commit and push changes
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: auto-update folder READMEs"
          branch: ${{ github.ref_name }}

	4.	Commit the file.

If your repository uses a different default branch, add it under branches: [ ... ].

⸻

🧷 Step 3 — Add Anchor Placeholders to Root README
	1.	Open your root README.md (homepage of repo) → click ✏️ Edit.
	2.	Add these lines (anywhere, e.g., at the bottom):

<!-- AUTO-INDEX:START -->

<!-- AUTO-INDEX:END -->

	3.	Commit changes.

The script will insert/update a “Runbook Folders” section between these anchors.

⸻

▶️ Step 4 — Trigger the Automation
	•	Add or edit any .md file inside your target folders (e.g., Firewall/).
	•	Push/commit the change.
	•	Go to Actions tab in GitHub → open the latest “Update folder READMEs” run → confirm it succeeded.
	•	Refresh your folder: Firewall/README.md should now list your runbooks.
	•	Check root README.md: a folder index appears between the anchors.

⸻

🧪 Quick Test Checklist
	•	Created scripts/gen_readmes.py
	•	Created .github/workflows/update-readmes.yml
	•	Added anchors in root README.md
	•	Pushed/edited a .md runbook
	•	Verified workflow ran (Actions tab)
	•	Verified folder README updated
	•	Verified root README block updated

⸻

🔧 Customization
	•	Change target folders: Edit FOLDERS = [...] in gen_readmes.py.
	•	Different headings/emojis: Modify header/notes strings in the script.
	•	Skip root README updates: Remove update_root_readme(REPO_ROOT) call in main().

⸻

🛠 Troubleshooting

Q: Workflow didn’t run.
	•	Ensure your change touched a file that matches the paths:
	•	**/*.md (any Markdown) or scripts/gen_readmes.py.
	•	Confirm default branch name is included under branches: [ main, master ].

Q: Workflow ran but couldn’t push changes.
	•	The workflow already has permissions: contents: write.
	•	In repo settings (if needed): Settings → Actions → General → Workflow permissions → ensure Read and write is allowed.

Q: Folder README didn’t change.
	•	Make sure the folder exists and has at least one *.md file (other than README.md).
	•	Confirm the folder name is present in FOLDERS.

Q: Root README didn’t update.
	•	Ensure the anchors exist exactly as:

<!-- AUTO-INDEX:START -->
<!-- AUTO-INDEX:END -->


	•	Ensure at least one folder in FOLDERS exists in the repo.

⸻

📎 Notes
	•	The script uses the first # heading inside each runbook as its display title.
	•	Keep the first line of each runbook clean, e.g., # 📘 Runbook – F5 Configuration Change Detected.
	•	You can manually re-run the workflow anytime from the Actions tab (use Run workflow).

⸻

📌 Maintenance
	•	When you add a new device folder (e.g., OT/), update FOLDERS in gen_readmes.py.
	•	Review/clean folder README wording as needed—these files are auto-managed by the script, so avoid manual edits; they will be overwritten on the next 

