# /// script
# dependencies = [
#   "click",
# ]
# ///

import re
from pathlib import Path

import click


def generate_adr_index():
    adr_dir = Path("docs/adr")
    readme_path = adr_dir / "README.md"

    adrs = []

    # Pattern to match ADR files: NNNN-title.md
    pattern = re.compile(r"^(\d{4})-(.*)\.md$")

    for file in sorted(adr_dir.glob("*.md")):
        match = pattern.match(file.name)
        if not match:
            continue

        num = match.group(1)

        with file.open(encoding="utf-8") as f:
            content = f.read()

        # Extract title (first line starting with #)
        title_match = re.search(r"^#\s*(.*)", content, re.MULTILINE)
        title = title_match.group(1) if title_match else file.name

        # Extract date
        date_match = re.search(r"^Date:\s*(.*)", content, re.MULTILINE)
        date = date_match.group(1) if date_match else "N/A"

        # Extract status
        status_match = re.search(r"##\s*Status\s*\n\n(.*?)\n", content, re.MULTILINE | re.DOTALL)
        status = status_match.group(1).strip() if status_match else "N/A"

        adrs.append({
            "num": num,
            "title": title,
            "date": date,
            "status": status,
            "filename": file.name
        })

    # Sort ADRs by number
    adrs.sort(key=lambda x: x["num"])

    # Generate README content
    lines = [
        "# Architecture Decision Records",
        "",
        "This directory contains the Architecture Decision Records for the dbt-helpers project.",
        "",
        "| ID | Title | Status | Date |",
        "| :--- | :--- | :--- | :--- |"
    ]

    for adr in adrs:
        # Link to the file
        title_link = f"[{adr['title']}]({adr['filename']})"
        lines.append(f"| {adr['num']} | {title_link} | {adr['status']} | {adr['date']} |")

    with readme_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    click.echo(f"Successfully generated {readme_path} with {len(adrs)} entries.")

@click.command()
def main():
    """Generate an index (README.md) for Architecture Decision Records in docs/adr/."""
    generate_adr_index()

if __name__ == "__main__":
    main()
