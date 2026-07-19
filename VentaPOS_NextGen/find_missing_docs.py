import os
import re

BASE_DIR = r"D:\Projects\VentaPOS\VentaPOS_NextGen"
DOCS_DIR = os.path.join(BASE_DIR, "docs")
FRONTEND_PAGES_DIR = os.path.join(BASE_DIR, "frontend", "src", "pages")
BACKEND_URLS_FILE = os.path.join(BASE_DIR, "backend", "api", "urls.py")

def get_all_markdown_files(docs_dir):
    md_files = []
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    return md_files

def get_frontend_pages(pages_dir):
    pages = set()
    for root, dirs, files in os.walk(pages_dir):
        for file in files:
            if file.endswith('.jsx'):
                name = file.replace('.jsx', '')
                pages.add(name)
    return pages

def get_backend_endpoints(urls_file):
    endpoints = set()
    with open(urls_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    routers = re.findall(r"router\.register\(\s*r'([^']+)'", content)
    for r in routers:
        endpoints.add(r)
        
    paths = re.findall(r"path\(\s*'([^']+)'", content)
    for p in paths:
        clean_p = p.replace('<int:pk>/', '').strip('/')
        if clean_p and clean_p != '':
            endpoints.add(clean_p)
            
    return endpoints

def read_all_docs(md_files):
    full_text = ""
    for file in md_files:
        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
            full_text += f.read() + "\n"
    return full_text

def main():
    md_files = get_all_markdown_files(DOCS_DIR)
    all_docs_text = read_all_docs(md_files)
    
    pages = get_frontend_pages(FRONTEND_PAGES_DIR)
    endpoints = get_backend_endpoints(BACKEND_URLS_FILE)
    
    missing_pages = []
    for page in pages:
        if page not in all_docs_text:
            missing_pages.append(page)
            
    missing_endpoints = []
    for ep in endpoints:
        if ep not in all_docs_text:
            missing_endpoints.append(ep)
            
    print("=== Missing Frontend Pages ===")
    for p in sorted(missing_pages):
        print(p)
        
    print("\n=== Missing Backend Endpoints ===")
    for ep in sorted(missing_endpoints):
        print(ep)

if __name__ == "__main__":
    main()
