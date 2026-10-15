import os
import re

FRONTEND_DIR = r"D:\Projects\VentaPOS\VentaPOS_NextGen\frontend"
BACKEND_DIR = r"D:\Projects\VentaPOS\VentaPOS_NextGen\backend"
DOCS_DIR = r"D:\Projects\VentaPOS\VentaPOS_NextGen\docs"
OUTPUT_FILE = r"D:\Projects\VentaPOS\.agents\worker_updates_1\output.txt"

def main():
    out = []
    
    # 1. Parse App.jsx
    app_jsx_path = os.path.join(FRONTEND_DIR, "src", "App.jsx")
    with open(app_jsx_path, 'r', encoding='utf-8') as f:
        app_content = f.read()

    # Extract component imports
    import_pattern = re.compile(r'import\s+([A-Za-z0-9_]+)\s+from\s+[\'"]([^\'"]+)[\'"]')
    components = []
    for name, path in import_pattern.findall(app_content):
        if path.startswith('.'):
            components.append(name)

    # Extract Route paths
    route_pattern = re.compile(r'<Route\s+[^>]*path=["\']([^"\']+)["\']')
    routes = route_pattern.findall(app_content)

    out.append("Discovered Frontend Components:")
    for c in sorted(components):
        out.append(f"  - {c}")
    out.append("\nDiscovered Frontend Routes:")
    for r in sorted(routes):
        out.append(f"  - {r}")

    # 2. Parse api/urls.py
    urls_path = os.path.join(BACKEND_DIR, "api", "urls.py")
    with open(urls_path, 'r', encoding='utf-8') as f:
        urls_content = f.read()

    # Extract router registrations
    router_pattern = re.compile(r'router\.register\(r[\'"]([^\'"]+)[\'"],\s*([A-Za-z0-9_]+)(?:,\s*basename=[\'"]([^\'"]+)[\'"])?\)')
    viewsets = []
    for path, viewset_class, basename in router_pattern.findall(urls_content):
        viewsets.append((path, viewset_class))

    # Extract path URLs
    path_pattern = re.compile(r'path\([\'"]([^\'"]+)[\'"],\s*([A-Za-z0-9_]+)(?:\.as_view\(\))?')
    path_views = []
    for path, view_class in path_pattern.findall(urls_content):
        path_views.append((path, view_class))

    out.append("\nDiscovered Backend Viewsets:")
    for path, vs in sorted(viewsets):
        out.append(f"  - {path} -> {vs}")
    out.append("\nDiscovered Backend Path Views:")
    for path, pv in sorted(path_views):
        out.append(f"  - {path} -> {pv}")

    # 3. Read docs
    docs_contents = {}
    for root, dirs, files in os.walk(DOCS_DIR):
        for f in files:
            if f.endswith('.md') and f != 'index.md':
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, DOCS_DIR).replace('\\', '/')
                with open(full_path, 'r', encoding='utf-8') as file_obj:
                    docs_contents[rel_path] = file_obj.read()

    out.append("\n--- Checking Frontend Components in Docs ---")
    undocumented_components = []
    for c in sorted(components):
        found = False
        for doc_name, doc_text in docs_contents.items():
            if c in doc_text:
                found = True
                break
        if not found:
            undocumented_components.append(c)
            out.append(f"Undocumented component: {c}")

    out.append("\n--- Checking Frontend Routes in Docs ---")
    undocumented_routes = []
    for r in sorted(routes):
        found = False
        for doc_name, doc_text in docs_contents.items():
            if r in doc_text:
                found = True
                break
        if not found:
            undocumented_routes.append(r)
            out.append(f"Undocumented route: {r}")

    out.append("\n--- Checking Backend Viewsets in Docs ---")
    undocumented_viewsets = []
    for path, vs in sorted(viewsets):
        found = False
        for doc_name, doc_text in docs_contents.items():
            if vs in doc_text or path in doc_text or f"/{path}/" in doc_text:
                found = True
                break
        if not found:
            undocumented_viewsets.append((path, vs))
            out.append(f"Undocumented viewset: {path} -> {vs}")

    out.append("\n--- Checking Backend Path Views in Docs ---")
    undocumented_path_views = []
    for path, pv in sorted(path_views):
        found = False
        for doc_name, doc_text in docs_contents.items():
            if pv in doc_text or path in doc_text:
                found = True
                break
        if not found:
            undocumented_path_views.append((path, pv))
            out.append(f"Undocumented path view: {path} -> {pv}")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out_f:
        out_f.write('\n'.join(out))

if __name__ == "__main__":
    main()
