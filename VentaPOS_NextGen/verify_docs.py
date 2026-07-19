import os
import re
import sys

# Get the script's directory (VentaPOS_NextGen root)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")

def get_frontend_components_and_routes():
    app_jsx_path = os.path.join(FRONTEND_DIR, "src", "App.jsx")
    if not os.path.exists(app_jsx_path):
        return [], []
        
    with open(app_jsx_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Extract imports of local pages/components
    components = []
    import_pat = re.compile(r'import\s+([A-Za-z0-9_]+)\s+from\s+[\'"]([^\'"]+)[\'"]')
    for name, path in import_pat.findall(content):
        if path.startswith('.'):
            components.append(name)
            
    # Extract routes
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
        
    # router.register(r'company-settings', CompanySettingViewSet)
    viewsets = []
    viewset_pat = re.compile(r'router\.register\(r[\'"]([^\'"]+)[\'"],\s*([A-Za-z0-9_]+)(?:,\s*basename=[\'"]([^\'"]+)[\'"])?\)')
    for path, viewset, basename in viewset_pat.findall(content):
        viewsets.append({
            "path": path,
            "viewset": viewset
        })
        
    # path('init/', SystemInitializationView.as_view(), name='system_init'),
    views = []
    path_pat = re.compile(r'path\([\'"]([^\'"]+)[\'"],\s*([A-Za-z0-9_]+)(?:\.as_view\(\))?')
    for path, view_class in path_pat.findall(content):
        views.append({
            "path": path,
            "view_class": view_class
        })
        
    return viewsets, views

def get_backend_views_and_actions():
    views_py_path = os.path.join(BACKEND_DIR, "api", "views.py")
    if not os.path.exists(views_py_path):
        return {}
        
    class_views = {}
    current_class = None
    actions = []
    
    with open(views_py_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
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
            
        # Check for @action
        if line.strip().startswith('@action'):
            # Look for def in the next few lines
            for j in range(i+1, min(i+10, len(lines))):
                def_match = re.match(r'^\s+def\s+([A-Za-z0-9_]+)\(', lines[j])
                if def_match:
                    action_name = def_match.group(1)
                    # Parse url_path from @action
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
    index_md = docs.get("index.md", "")
    
    # Extract TODO section
    todo_section = ""
    if "## 5. Missing Documentation (TODO)" in index_md:
        todo_section = index_md.split("## 5. Missing Documentation (TODO)")[1]
        
    # Unified non-index docs text
    non_index_docs_text = "\n\n".join([content for path, content in docs.items() if path != "index.md"])
    # Documented text before TODO list in index.md
    index_docs_text_before_todo = index_md.split("## 5. Missing Documentation (TODO)")[0] if "## 5. Missing Documentation (TODO)" in index_md else index_md
    docs_text_excluding_todo = non_index_docs_text + "\n\n" + index_docs_text_before_todo
    
    # Extract active frontend routes/components
    components, routes = get_frontend_components_and_routes()
    
    # Extract backend API endpoints
    viewsets, path_views = get_backend_urls()
    backend_classes = get_backend_views_and_actions()
    
    missing_items = []
    
    # 1. Verify Frontend Components
    print("\nVerifying Frontend Components...")
    for comp in components:
        queries = [comp, f"{comp}.jsx"]
        in_docs = search_text_in_text(queries, docs_text_excluding_todo)
        in_todo = search_text_in_text(queries, todo_section)
        
        if in_docs:
            print(f"  [OK] Component '{comp}' is documented.")
        elif in_todo:
            print(f"  [OK] Component '{comp}' is listed in TODO.")
        else:
            print(f"  [FAIL] Component '{comp}' is undocumented and not in TODO!")
            missing_items.append(f"Frontend Component: {comp}")
            
    # 2. Verify Frontend Routes
    print("\nVerifying Frontend Routes...")
    for route in routes:
        # Ignore root route or empty routes
        if route == "/":
            continue
        # Normalize route: remove leading slash, parameters, wildcards
        norm_route = route.lstrip('/').split('/:')[0].split('/*')[0]
        queries = [route, norm_route]
        in_docs = search_text_in_text(queries, docs_text_excluding_todo)
        in_todo = search_text_in_text(queries, todo_section)
        
        if in_docs:
            print(f"  [OK] Route '{route}' is documented.")
        elif in_todo:
            print(f"  [OK] Route '{route}' is listed in TODO.")
        else:
            print(f"  [FAIL] Route '{route}' is undocumented and not in TODO!")
            missing_items.append(f"Frontend Route: {route}")
            
    # 3. Verify Backend Viewsets & Actions
    print("\nVerifying Backend Viewsets & Custom Actions...")
    for vs in viewsets:
        path = vs["path"]
        vs_class = vs["viewset"]
        queries = [vs_class, path, f"/api/v1/{path}/", f"/api/{path}/"]
        in_docs = search_text_in_text(queries, docs_text_excluding_todo)
        in_todo = search_text_in_text(queries, todo_section)
        
        if in_docs:
            print(f"  [OK] Viewset '{vs_class}' ({path}) is documented.")
        elif in_todo:
            print(f"  [OK] Viewset '{vs_class}' ({path}) is listed in TODO.")
        else:
            print(f"  [FAIL] Viewset '{vs_class}' ({path}) is undocumented and not in TODO!")
            missing_items.append(f"Backend Viewset: {vs_class} ({path})")
            
        # Check custom actions for this Viewset
        if vs_class in backend_classes:
            for act in backend_classes[vs_class]["actions"]:
                action_name = act["name"]
                action_path = f"/api/v1/{path}/{act['url_path']}/"
                norm_action_path = f"/api/{path}/{act['url_path']}/"
                
                act_queries = [action_name, action_path, norm_action_path]
                act_in_docs = search_text_in_text(act_queries, docs_text_excluding_todo)
                act_in_todo = search_text_in_text(act_queries, todo_section)
                
                if act_in_docs:
                    print(f"    [OK] Action '{action_name}' ({action_path}) is documented.")
                elif act_in_todo:
                    print(f"    [OK] Action '{action_name}' ({action_path}) is listed in TODO.")
                else:
                    print(f"    [FAIL] Action '{action_name}' ({action_path}) is undocumented and not in TODO!")
                    missing_items.append(f"Backend Action: {vs_class}.{action_name} ({action_path})")
                    
    # 4. Verify Backend Path Views
    print("\nVerifying Backend Path Views...")
    for pv in path_views:
        path = pv["path"]
        view_class = pv["view_class"]
        queries = [view_class, path, f"/api/v1/{path}", f"/api/{path}"]
        in_docs = search_text_in_text(queries, docs_text_excluding_todo)
        in_todo = search_text_in_text(queries, todo_section)
        
        if in_docs:
            print(f"  [OK] Path View '{view_class}' ({path}) is documented.")
        elif in_todo:
            print(f"  [OK] Path View '{view_class}' ({path}) is listed in TODO.")
        else:
            print(f"  [FAIL] Path View '{view_class}' ({path}) is undocumented and not in TODO!")
            missing_items.append(f"Backend Path View: {view_class} ({path})")
            
    print("\n-------------------------------------------")
    if missing_items:
        print(f"Verification FAILED. {len(missing_items)} undocumented/unlisted item(s) found:")
        for item in missing_items:
            print(f"  - {item}")
        sys.exit(1)
    else:
        print("Verification PASSED. 100% of active routes, components, and endpoints are documented or listed in TODO.")
        sys.exit(0)

if __name__ == "__main__":
    main()
