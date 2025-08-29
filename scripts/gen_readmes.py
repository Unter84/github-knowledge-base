#!/usr/bin/env python3
import os, re, pathlib, sys
from datetime import datetime

# Folders you want indexed
FOLDERS = ["Firewall", "Windows", "Linux", "Cloud", "Email", "Endpoint", "Network"]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

def title_from_md(path: pathlib.Path) -> str:
    # Use first Markdown heading as the title; fallback to file name
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.strip().startswith("#"):
                    # Strip leading #'s and whitespace/emojis
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
            rel = md.name  # relative link within the folder
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
    # Optional: keep a simple index of folders in the root README if it exists.
    root_readme = root / "README.md"
    if not root_readme.exists():
        return
    # Build a small section listing folders
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
        # Replace existing block
        content = re.sub(
            rf"{re.escape(block_start)}.*?{re.escape(block_end)}",
            injected,
            content,
            flags=re.S,
        )
    else:
        # Append block to the end
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

    # Optional root README index update
    update_root_readme(REPO_ROOT)
    return 0 if changed else 0

if __name__ == "__main__":
    sys.exit(main())
