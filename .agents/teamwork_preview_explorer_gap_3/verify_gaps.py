import os
import re
import json

# Paths
WORKSPACE = "D:/Projects/VentaPOS"
NEXTGEN_DIR = os.path.join(WORKSPACE, "VentaPOS_NextGen")
FRONTEND_DIR = os.path.join(NEXTGEN_DIR, "frontend")
BACKEND_DIR = os.path.join(NEXTGEN_DIR, "backend")
DOCS_DIR = os.path.join(NEXTGEN_DIR, "docs")

def get_frontend_components_and_routes():
    app_jsx_path = os.path.join(FRONTEND_DIR, "src/App.jsx")
    if not os.path.exists(app_jsx_path):
        return [], []
        
    with open(app_jsx_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Extract imports
    imports = []
    # e.g., import Login from './pages/Login';
    import_pat = re.compile(r'import\s+([A-Za-z0-9_]+)\s+from\s+[\'"]([^\'"]+)[\'"]')
    for name, path in import_pat.findall(content):
        if path.startswith('.'):
            clean_path = path.lstrip('./').lstrip('../')
            imports.append({
                "component": name,
                "import_path": path,
                "resolved_path": clean_path
            })
            
    # Extract routes
    routes = []
    route_pat = re.compile(r'<Route\s+[^>]*path=["\']([^"\']+)["\']')
    for r_path in route_pat.findall(content):
        routes.append(r_path)
        
    return imports, routes

def get_all_frontend_files():
    src_dir = os.path.join(FRONTEND_DIR, "src")
    files_list = []
    if not os.path.exists(src_dir):
        return files_list
        
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            if f.endswith(('.js', '.jsx', '.ts', '.tsx')):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, src_dir)
                files_list.append({
                    "filename": f,
                    "rel_path": rel_path.replace('\\', '/')
                })
    return files_list

def get_backend_urls():
    urls_py_path = os.path.join(BACKEND_DIR, "api/urls.py")
    if not os.path.exists(urls_py_path):
        return [], []
        
    with open(urls_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # router.register(r'company-settings', CompanySettingViewSet)
    viewsets = []
    # Improved regex to handle optional parameters like basename
    viewset_pat = re.compile(r'router\.register\(r[\'"]([^\'"]+)[\'"],\s*([A-Za-z0-9_]+ViewSet)(?:,\s*[^)]*)?\)')
    for path, viewset in viewset_pat.findall(content):
        viewsets.append({
            "path": f"/api/v1/{path}/",
            "normalized_path": f"/api/{path}/",
            "viewset": viewset
        })
        
    # path('init/', SystemInitializationView.as_view(), name='system_init'),
    views = []
    path_pat = re.compile(r'path\([\'"]([^\'"]+)[\'"],\s*([A-Za-z0-9_]+)(?:\.as_view\(\))?')
    for path, view_class in path_pat.findall(content):
        views.append({
            "path": f"/api/v1/{path}",
            "normalized_path": f"/api/{path}",
            "view_class": view_class
        })
        
    return viewsets, views

def get_backend_views_and_actions():
    views_py_path = os.path.join(BACKEND_DIR, "api/views.py")
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

def search_text_in_docs(text_queries, docs_text):
    # Check if any of the query terms are in the docs text
    for q in text_queries:
        if q in docs_text:
            return True
    return False

def main():
    print("Starting Gap Analysis Script...")
    
    # 1. Load documentation
    docs = get_docs_content()
    index_md = docs.get("index.md", "")
    
    # Extract TODO section in index.md
    todo_section = ""
    if "## 5. Missing Documentation (TODO)" in index_md:
        todo_section = index_md.split("## 5. Missing Documentation (TODO)")[1]
    
    # Create a unified docs content excluding index.md for searching
    non_index_docs_text = "\n\n".join([content for path, content in docs.items() if path != "index.md"])
    
    # 2. Extract frontend info
    imports, routes = get_frontend_components_and_routes()
    all_frontend_files = get_all_frontend_files()
    
    # 3. Extract backend info
    viewsets, path_views = get_backend_urls()
    backend_classes = get_backend_views_and_actions()
    
    # 4. Perform analysis on frontend pages
    frontend_gaps = []
    for f_info in all_frontend_files:
        filename = f_info["filename"]
        rel_path = f_info["rel_path"]
        
        # We only check files under pages/ or components/
        if not (rel_path.startswith("pages/") or rel_path.startswith("components/")):
            continue
            
        queries = [filename, filename.replace('.jsx', '')]
        in_docs = search_text_in_docs(queries, non_index_docs_text)
        in_todo = search_text_in_docs(queries, todo_section)
        
        frontend_gaps.append({
            "filename": filename,
            "rel_path": rel_path,
            "in_docs": in_docs,
            "in_todo": in_todo
        })
        
    # 5. Perform analysis on backend routes
    backend_gaps = []
    
    # Registered viewsets
    for vs in viewsets:
        path = vs["path"]
        norm_path = vs["normalized_path"]
        viewset_class = vs["viewset"]
        
        # Check for paths and class name in docs
        queries = [path, norm_path, viewset_class]
        in_docs = search_text_in_docs(queries, non_index_docs_text)
        in_todo = search_text_in_docs(queries, todo_section)
        
        # Check custom actions
        actions = []
        if viewset_class in backend_classes:
            for act in backend_classes[viewset_class]["actions"]:
                action_path = f"{path}{act['url_path']}/"
                norm_action_path = f"{norm_path}{act['url_path']}/"
                
                act_queries = [action_path, norm_action_path, act['name']]
                act_in_docs = search_text_in_docs(act_queries, non_index_docs_text)
                act_in_todo = search_text_in_docs(act_queries, todo_section)
                actions.append({
                    "name": act["name"],
                    "path": action_path,
                    "in_docs": act_in_docs,
                    "in_todo": act_in_todo
                })
                
        backend_gaps.append({
            "type": "ViewSet",
            "class_name": viewset_class,
            "path": path,
            "in_docs": in_docs,
            "in_todo": in_todo,
            "actions": actions,
            "registered": True
        })
        
    # Registered path views
    for pv in path_views:
        path = pv["path"]
        norm_path = pv["normalized_path"]
        view_class = pv["view_class"]
        
        queries = [path, norm_path, view_class]
        in_docs = search_text_in_docs(queries, non_index_docs_text)
        in_todo = search_text_in_docs(queries, todo_section)
        
        backend_gaps.append({
            "type": "APIView",
            "class_name": view_class,
            "path": path,
            "in_docs": in_docs,
            "in_todo": in_todo,
            "actions": [],
            "registered": True
        })
        
    # Unmapped views (defined in views.py but not urls.py)
    registered_classes = set([vs["viewset"] for vs in viewsets] + [pv["view_class"] for pv in path_views])
    unmapped_gaps = []
    for class_name, info in backend_classes.items():
        if class_name not in registered_classes:
            if class_name in ["TenantFromRequestMixin", "SoftDeleteModelViewSet", "PurchaseInvoicePagination", "ReceiptPagination"]:
                continue
            
            in_docs = class_name in non_index_docs_text
            in_todo = class_name in todo_section
            unmapped_gaps.append({
                "class_name": class_name,
                "parent": info["parent"],
                "in_docs": in_docs,
                "in_todo": in_todo
            })
            
    # Output results
    results = {
        "frontend": frontend_gaps,
        "backend": backend_gaps,
        "unmapped": unmapped_gaps
    }
    
    output_path = "D:/Projects/VentaPOS/.agents/teamwork_preview_explorer_gap_3/analysis_results.json"
    with open(output_path, 'w', encoding='utf-8') as out_f:
        json.dump(results, out_f, indent=2, ensure_ascii=False)
        
    print(f"Analysis complete. Results written to {output_path}")

if __name__ == "__main__":
    main()
