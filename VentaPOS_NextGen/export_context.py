#!/usr/bin/env python3
"""
VentaPOS NextGen — Context Exporter
Bundles all active documentation, desktop configuration, core Django backend,
and React frontend source code into a unified Markdown file for LLM context.
"""

import os
from pathlib import Path

EXT_LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "jsx",
    ".css": "css",
    ".json": "json",
    ".html": "html",
    ".md": "markdown",
    ".spec": "python",
}

def get_fence(content: str) -> str:
    """Return a fence that doesn't conflict with backticks inside content."""
    count = 3
    while "`" * count in content:
        count += 1
    return "`" * count

def collect_files(root: Path):
    target_files = []

    # 1. Core Rules & Docs
    explicit_docs = [
        root / ".agents" / "AGENTS.md",
        root / ".agents" / "CODEBASE_MAP.md",
        root / "VentaPOS_NextGen" / "TODO.md",
        root / "VentaPOS_NextGen" / "UI_UX_RULES.md",
        root / "VentaPOS_NextGen" / "REPORTS_AGREEMENT.md",
        root / "VentaPOS_NextGen" / "frontend" / "TABLE_UX_GUIDELINES.md",
    ]
    for p in explicit_docs:
        if p.is_file():
            target_files.append(p)

    conductor_dir = root / "VentaPOS_NextGen" / "conductor"
    if conductor_dir.is_dir():
        for p in sorted(conductor_dir.rglob("*.md")):
            if p.is_file():
                target_files.append(p)

    docs_arch_dir = root / "VentaPOS_NextGen" / "docs" / "architecture"
    if docs_arch_dir.is_dir():
        for p in sorted(docs_arch_dir.rglob("*.md")):
            if p.is_file():
                target_files.append(p)

    # 2. Desktop Packaging
    desktop_files = [
        root / "VentaPOS_NextGen" / "launcher.py",
        root / "VentaPOS_NextGen" / "build_exe.py",
        root / "VentaPOS_NextGen" / "VentaPOS.spec",
    ]
    for p in desktop_files:
        if p.is_file():
            target_files.append(p)

    # 3. Django Backend Core
    backend_explicit = [
        root / "VentaPOS_NextGen" / "backend" / "backend" / "settings.py",
        root / "VentaPOS_NextGen" / "backend" / "backend" / "urls.py",
        root / "VentaPOS_NextGen" / "backend" / "api" / "models.py",
        root / "VentaPOS_NextGen" / "backend" / "api" / "serializers.py",
        root / "VentaPOS_NextGen" / "backend" / "api" / "views.py",
        root / "VentaPOS_NextGen" / "backend" / "api" / "tools_views.py",
        root / "VentaPOS_NextGen" / "backend" / "api" / "logger_views.py",
        root / "VentaPOS_NextGen" / "backend" / "api" / "urls.py",
        root / "VentaPOS_NextGen" / "backend" / "api" / "middleware.py",
        root / "VentaPOS_NextGen" / "backend" / "api" / "print_utils.py",
    ]
    for p in backend_explicit:
        if p.is_file():
            target_files.append(p)

    backend_utils = root / "VentaPOS_NextGen" / "backend" / "api" / "utils"
    if backend_utils.is_dir():
        for p in sorted(backend_utils.glob("*.py")):
            if p.is_file():
                target_files.append(p)

    # 4. React Frontend Core
    frontend_explicit = [
        root / "VentaPOS_NextGen" / "frontend" / "package.json",
        root / "VentaPOS_NextGen" / "frontend" / "index.html",
        root / "VentaPOS_NextGen" / "frontend" / "vite.config.js",
    ]
    for p in frontend_explicit:
        if p.is_file():
            target_files.append(p)

    frontend_src = root / "VentaPOS_NextGen" / "frontend" / "src"
    if frontend_src.is_dir():
        for ext in ("*.js", "*.jsx", "*.css"):
            for p in sorted(frontend_src.rglob(ext)):
                if p.is_file():
                    target_files.append(p)

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for p in target_files:
        canonical = p.resolve()
        if canonical not in seen:
            seen.add(canonical)
            deduped.append(p)

    return deduped

def main():
    script_dir = Path(__file__).resolve().parent
    if script_dir.name == "VentaPOS_NextGen":
        root = script_dir.parent
    else:
        root = Path(os.getcwd())

    output_path = root / "VENTAPOS_CONTEXT.md"
    files = collect_files(root)

    print(f"Collecting {len(files)} active project files...")

    total_lines = 0
    with open(output_path, "w", encoding="utf-8") as out:
        out.write("# VentaPOS NextGen — Complete Active Project Context\n\n")
        out.write(f"> **Snapshot Export**: {len(files)} active files\n")
        out.write("> **Scope**: Rules, Docs, Packaging, Django Backend, React Frontend\n\n")
        out.write("---\n\n")

        for fpath in files:
            rel_path = fpath.relative_to(root).as_posix()
            lang = EXT_LANG_MAP.get(fpath.suffix.lower(), "")
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception as err:
                print(f"Warning: could not read {rel_path}: {err}")
                continue

            fence = get_fence(content)
            line_count = len(content.splitlines())
            total_lines += line_count

            out.write(f"## FILE: {rel_path}\n\n")
            out.write(f"{fence}{lang}\n")
            out.write(content)
            if not content.endswith("\n"):
                out.write("\n")
            out.write(f"{fence}\n\n")

    size_bytes = output_path.stat().st_size
    size_kb = size_bytes / 1024
    size_mb = size_kb / 1024

    print("=" * 60)
    print(f"Export successful!")
    print(f"Target file:  {output_path}")
    print(f"Files packed: {len(files)}")
    print(f"Total lines:  {total_lines:,}")
    print(f"File size:    {size_bytes:,} bytes ({size_kb:.2f} KB / {size_mb:.2f} MB)")
    print("=" * 60)

if __name__ == "__main__":
    main()
