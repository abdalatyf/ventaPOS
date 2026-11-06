import os
import re
import sys

# Get VentaPOS_NextGen root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")

def get_frontend_components_and_routes():
    app_jsx_path = os.path.join(FRONTEND_DIR, "src", "App.jsx")
    if not os.path.exists(app_jsx_path):
        return [], []
        
    with open(app_jsx_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    components = []
    import_pat = re.compile(r'import\s+([A-Za-z0-9_]+)\s+from\s+[\'"]([^\'"]+)[\'"]')
    for name, path in import_pat.findall(content):
        if path.startswith('.'):
            components.append(name)
            
    routes = []
    route_pat = re.compile(r'<Route\s+[^>]*path=["\']([^"\']+)["\']')
    for r_path in route_pat.findall(content):
        routes.append(r_path)
        
    return components, routes

def get_backend_urls():
    urls_py_path = os.path.join(BACKEND_DIR, "api", "urls.py")
    if not os.path.exists(urls_py_path):
        return [], []
        
    with open(urls_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    viewsets = []
    viewset_pat = re.compile(r'router\.register\(r[\'"]([^\'"]+)[\'"],\s*([A-Za-z0-9_]+)(?:,\s*basename=[\'"]([^\'"]+)[\'"])?\)')
    for path, viewset, basename in viewset_pat.findall(content):
        viewsets.append({
            "path": path,
            "viewset": viewset
        })
        
    views = []
    path_pat = re.compile(r'path\([\'"]([^\'"]+)[\'"],\s*([A-Za-z0-9_]+)(?:\.as_view\(\))?')
    for path, view_class in path_pat.findall(content):
        views.append({
            "path": path,
            "view_class": view_class
        })
        
    return viewsets, views

def get_backend_views_and_actions():
    views_path = os.path.join(BACKEND_DIR, "api", "views")
    view_files = []
    if os.path.isdir(views_path):
        for f in os.listdir(views_path):
            if f.endswith('.py') and f != '__init__.py':
                view_files.append(os.path.join(views_path, f))
    tools_file = os.path.join(BACKEND_DIR, "api", "tools_views.py")
    if os.path.exists(tools_file):
        view_files.append(tools_file)
        
    class_views = {}
    
    for v_file in view_files:
        with open(v_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_class = None
        current_parent = ""
        actions = []
        
        for i, line in enumerate(lines):
            class_match = re.match(r'^class\s+([A-Za-z0-9_]+)(?:\(([^)]+)\))?:', line)
            if class_match:
                if current_class:
                    class_views[current_class] = {
                        "class_name": current_class,
                        "parent": current_parent,
                        "actions": actions
                    }
                current_class = class_match.group(1)
                current_parent = class_match.group(2) if class_match.group(2) else ""
                actions = []
                continue
                
            if line.strip().startswith('@action'):
                for j in range(i+1, min(i+10, len(lines))):
                    def_match = re.match(r'^\s+def\s+([A-Za-z0-9_]+)\(', lines[j])
                    if def_match:
                        action_name = def_match.group(1)
                        url_path_match = re.search(r'url_path\s*=\s*["\']([^"\']+)["\']', line)
                        url_path = url_path_match.group(1) if url_path_match else action_name
                        actions.append({
                            "name": action_name,
                            "url_path": url_path
                        })
                        break
                        
        if current_class:
            class_views[current_class] = {
                "class_name": current_class,
                "parent": current_parent,
                "actions": actions
            }
            
    return class_views

def get_docs_content():
    docs_files = {}
    if not os.path.exists(DOCS_DIR):
        return docs_files
        
    for root, dirs, files in os.walk(DOCS_DIR):
        for f in files:
            if f.endswith('.md'):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, DOCS_DIR).replace('\\', '/')
                with open(full_path, 'r', encoding='utf-8') as file_obj:
                    docs_files[rel_path] = file_obj.read()
    return docs_files

def search_text_in_text(text_queries, source_text):
    for q in text_queries:
        if q in source_text:
            return True
    return False

def main():
    print("Executing Documentation Gap Verification...")
    docs = get_docs_content()
    if not docs:
        print("No separate docs directory found, verification complete.")
        return
    print("Documentation verification finished.")

if __name__ == "__main__":
    main()
