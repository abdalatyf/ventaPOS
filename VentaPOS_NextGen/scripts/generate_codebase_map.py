import os
import ast
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_API = BASE_DIR / "backend" / "api"
FRONTEND_SRC = BASE_DIR / "frontend" / "src"
OUT_FILE = BASE_DIR.parent / ".agents" / "CODEBASE_MAP.md"


def parse_models():
    models_file = BACKEND_API / "models.py"
    if not models_file.exists():
        return "Models not found.\n"
    out = "## 1. Backend Models (`backend/api/models.py`)\n\n"
    try:
        with open(models_file, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [
                    b.id if isinstance(b, ast.Name) else getattr(b.value, 'id', '') + '.' + getattr(b, 'attr', '')
                    for b in node.bases
                    if hasattr(b, 'id') or hasattr(b, 'attr')
                ]
                if any('Model' in b for b in bases):
                    out += f"### {node.name}\n"
                    for body_node in node.body:
                        if isinstance(body_node, ast.Assign) and isinstance(body_node.targets[0], ast.Name):
                            field_name = body_node.targets[0].id
                            field_type = "Field"
                            if isinstance(body_node.value, ast.Call):
                                if isinstance(body_node.value.func, ast.Attribute):
                                    field_type = body_node.value.func.attr
                                elif isinstance(body_node.value.func, ast.Name):
                                    field_type = body_node.value.func.id
                            out += f"- `{field_name}` ({field_type})\n"
                    out += "\n"
    except Exception as e:
        out += f"Error parsing models: {e}\n"
    return out


def parse_views():
    out = "## 2. Backend Views & ViewSets (`backend/api/views/` & `tools_views.py`)\n\n"
    view_files = []
    views_dir = BACKEND_API / "views"
    if views_dir.exists():
        view_files.extend(sorted(views_dir.glob("*.py")))
    tools_file = BACKEND_API / "tools_views.py"
    if tools_file.exists():
        view_files.append(tools_file)

    for vf in view_files:
        if vf.name == "__init__.py":
            continue
        rel_path = vf.relative_to(BASE_DIR)
        out += f"### File: `{rel_path}`\n\n"
        try:
            with open(vf, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = []
                    for bnode in node.body:
                        if isinstance(bnode, ast.FunctionDef) and not bnode.name.startswith("__"):
                            methods.append(bnode.name)
                    methods_str = f" (`{', '.join(methods)}`)" if methods else ""
                    out += f"- **`{node.name}`**{methods_str}\n"
            out += "\n"
        except Exception as e:
            out += f"- Error reading {vf.name}: {e}\n\n"
    return out


def parse_services():
    out = "## 3. Backend Domain Services (`backend/api/services/`)\n\n"
    services_dir = BACKEND_API / "services"
    if not services_dir.exists():
        return out + "No services directory found.\n\n"

    for sf in sorted(services_dir.glob("*.py")):
        if sf.name == "__init__.py":
            continue
        rel_path = sf.relative_to(BASE_DIR)
        out += f"### Service: `{rel_path}`\n\n"
        try:
            with open(sf, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    args = [a.arg for a in node.args.args]
                    out += f"- `def {node.name}({', '.join(args)})`\n"
            out += "\n"
        except Exception as e:
            out += f"- Error reading {sf.name}: {e}\n\n"
    return out


def parse_urls():
    urls_file = BACKEND_API / "urls.py"
    if not urls_file.exists():
        return "URLs not found.\n"
    out = "## 4. Backend API Endpoints (`backend/api/urls.py`)\n\n"
    try:
        with open(urls_file, "r", encoding="utf-8") as f:
            content = f.read()

        router_regs = re.findall(r'router\.register\(\s*r?[\'"]([^\'"]+)[\'"],\s*([^,\)]+)', content)
        if router_regs:
            out += "### REST Router ViewSets:\n"
            for prefix, viewset in router_regs:
                out += f"- `api/v1/{prefix}/` -> `{viewset.strip()}`\n"
            out += "\n"

        paths = re.findall(r'path\(\s*[\'"]([^\'"]*)[\'"],\s*([^,\)]+)', content)
        if paths:
            out += "### Direct API Views:\n"
            for p, handler in paths:
                handler = re.sub(r'as_view\([^)]*\)', 'as_view()', handler)
                out += f"- `api/v1/{p}` -> `{handler.strip()}`\n"
            out += "\n"
    except Exception as e:
        out += f"Error parsing urls: {e}\n"
    return out


def parse_serializers_and_middleware():
    out = "## 5. Serializers, Middleware & Print Utils\n\n"
    for filename in ("serializers.py", "middleware.py", "print_utils.py"):
        filepath = BACKEND_API / filename
        if not filepath.exists():
            continue
        out += f"### `backend/api/{filename}`\n"
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")]
            if classes:
                out += f"- Classes: `{', '.join(classes)}`\n"
            if functions:
                out += f"- Functions: `{', '.join(functions)}`\n"
            out += "\n"
        except Exception as e:
            out += f"- Error: {e}\n\n"
    return out


def parse_frontend():
    out = "## 6. Frontend Architecture (`frontend/src/`)\n\n"
    pages_dir = FRONTEND_SRC / "pages"
    components_dir = FRONTEND_SRC / "components"
    hooks_dir = FRONTEND_SRC / "hooks"

    out += "### Pages (`frontend/src/pages/`):\n"
    if pages_dir.exists():
        for p in sorted(pages_dir.rglob("*.jsx")):
            rel = p.relative_to(pages_dir)
            out += f"- `{rel}`\n"
    out += "\n"

    out += "### Components (`frontend/src/components/`):\n"
    if components_dir.exists():
        for c in sorted(components_dir.rglob("*.jsx")):
            rel = c.relative_to(components_dir)
            out += f"- `{rel}`\n"
    out += "\n"

    out += "### Custom Hooks (`frontend/src/hooks/`):\n"
    if hooks_dir.exists():
        for h in sorted(hooks_dir.glob("*.js")):
            out += f"- `{h.name}`\n"
    out += "\n"
    return out


def main():
    print(f"Generating updated codebase map to {OUT_FILE}...")
    content = "# VentaPOS NextGen — Codebase Interface Map\n\n"
    content += "> **This is a compressed, interface-only representation of the VentaPOS NextGen codebase (~10KB).**\n"
    content += "> Agents must read this file instead of navigating raw source files to prevent context bloat.\n\n"

    content += parse_models()
    content += parse_views()
    content += parse_services()
    content += parse_urls()
    content += parse_serializers_and_middleware()
    content += parse_frontend()

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print("Codebase map successfully generated!")


if __name__ == "__main__":
    main()
