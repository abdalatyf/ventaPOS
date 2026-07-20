import urllib.request
import socket

def find_port():
    for port in range(1024, 65535):
        try:
            req = urllib.request.Request(f'http://127.0.0.1:{port}/', method='GET')
            with urllib.request.urlopen(req, timeout=0.01) as response:
                html = response.read().decode('utf-8')
                if 'VentaPOS' in html or 'vite' in html or 'root' in html:
                    print(f'FOUND_PORT: {port}')
                    return port
        except Exception:
            pass
    print("NOT_FOUND")

if __name__ == '__main__':
    find_port()
