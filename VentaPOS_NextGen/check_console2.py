from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def get_console_logs():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Enable performance logging
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    
    try:
        driver = webdriver.Chrome(options=options)
        # Assuming token is in localStorage, but maybe not? We just need to catch the error.
        driver.get('http://localhost:5173/pos')
        
        # Inject dummy token and branchId so it doesn't redirect
        driver.execute_script("localStorage.setItem('token', 'dummy_token');")
        driver.execute_script("localStorage.setItem('branchId', '1');")
        # Reload so POS actually mounts
        driver.get('http://localhost:5173/pos')
        
        import time
        time.sleep(3)
        
        # Get logs
        logs = driver.get_log('browser')
        if not logs:
            print("No console logs found.")
        for log in logs:
            print(f"[{log['level']}] {log['message']}")
            
        driver.quit()
    except Exception as e:
        print(f"Selenium error: {e}")

if __name__ == "__main__":
    get_console_logs()
