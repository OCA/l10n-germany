#!/usr/bin/env python3
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# pylint: disable=print-used
"""Regenerate the model, settings view and DESCRIPTION.md from config.yml.

Requires PyYAML and Jinja2. Run from anywhere:

    python3 l10n_de_accounting_app/dev_tools/generate.py

Pre-commit is invoked on the generated files so the Python is reflowed by
ruff-format and the XML by prettier.
"""

import re
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yml"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

OUTPUTS = {
    "res_config_settings.py.j2": ROOT / "models" / "res_config_settings.py",
    "res_config_settings_views.xml.j2": ROOT
    / "views"
    / "res_config_settings_views.xml",
    "DESCRIPTION.md.j2": ROOT / "readme" / "DESCRIPTION.md",
}


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _md_inline_to_html(text):
    out = xml_escape(text)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", out)
    out = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        out,
    )
    out = re.sub(
        r"&lt;(https?://.+?)&gt;",
        r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>',
        out,
    )
    return out


def md_to_html(text):
    if not text:
        return ""
    parts = []
    for block in re.split(r"\n\n+", text.strip()):
        lines = block.split("\n")
        if all(line.startswith("- ") for line in lines):
            items = "".join(
                f"<li>{_md_inline_to_html(line[2:])}</li>" for line in lines
            )
            parts.append(f'<ul class="mb-0">{items}</ul>')
        else:
            parts.append(_md_inline_to_html(block.replace("\n", " ")))
    return "".join(parts)


def py_str(text):
    """Escape a string for use inside a Python double-quoted literal."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def enrich(cfg):
    app_name = cfg["app"]["name"]
    cfg["module_fields"] = []
    for section in cfg["sections"]:
        section["block_id"] = f"{app_name}_{slugify(section['name'])}"
        section.setdefault("repo", None)
        section.setdefault("source", None)
        section.setdefault("description", None)
        if section["repo"]:
            section["repo_label"] = f"OCA/{section['repo']}"
            section["repo_url"] = f"https://github.com/{section['repo_label']}"
        for addon in section["addons"]:
            cfg["module_fields"].append(f"module_{addon['name']}")
    return cfg


def main():
    cfg = enrich(yaml.safe_load(CONFIG_PATH.read_text()))
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    env.filters["md_to_html"] = md_to_html
    env.filters["py_str"] = py_str

    for template_name, output_path in OUTPUTS.items():
        rendered = env.get_template(template_name).render(**cfg)
        output_path.write_text(rendered.rstrip() + "\n")
        print(f"Wrote {output_path.relative_to(ROOT)}", flush=True)

    run_pre_commit(OUTPUTS.values())


def run_pre_commit(files):
    try:
        subprocess.run(
            ["pre-commit", "run", "--files", *map(str, files)],
            cwd=ROOT,
            check=False,
        )
    except FileNotFoundError:
        print("pre-commit not installed; skipping.")


if __name__ == "__main__":
    main()
