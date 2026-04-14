import urllib.request
import urllib.parse
import http.cookiejar
import re
import time

class HTTPClient:
    def __init__(self, base_url="http://localhost/"):
        self.base_url = base_url.rstrip('/') + '/'
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.login_url = f"{self.base_url}login.php"
        self.security_url = f"{self.base_url}security.php"
        self.injection_url = f"{self.base_url}vulnerabilities/sqli/"

    def _get_token(self, url):
        """Extracts user_token from the specified page using regex."""
        try:
            with self.opener.open(url) as response:
                html = response.read().decode('utf-8', errors='ignore')
                match = re.search(r'name=["\']user_token["\']\s+value=["\']([^"\']+)["\']', html)
                if not match:
                    match = re.search(r'value=["\']([^"\']+)["\']\s+name=["\']user_token["\']', html)
                return match.group(1) if match else None
        except Exception as e:
            print(f"[!] Error extracting CSRF token: {e}")
            return None

    def setup_dvwa(self, username="admin", password="password", security_level="medium"):
        """Performs login and sets security level."""
        print(f"[*] Initializing connection to {self.base_url}...")
        
        # 1. Login
        token = self._get_token(self.login_url)
        login_data = {
            'username': username,
            'password': password,
            'Login': 'Login'
        }
        if token:
            login_data['user_token'] = token
            
        print(f"[*] Attempting login as '{username}'...")
        try:
            encoded_data = urllib.parse.urlencode(login_data).encode('utf-8')
            with self.opener.open(self.login_url, data=encoded_data) as res:
                content = res.read().decode('utf-8', errors='ignore')
                if "Login failed" in content:
                    print("[!] Login failed. Check credentials.")
                    return False
        except Exception as e:
            print(f"[!] Login error: {e}")
            return False
            
        # 2. Set Security Level
        print(f"[*] Setting Security Level to: {security_level.upper()}")
        token = self._get_token(self.security_url)
        security_data = {
            'security': security_level.lower(),
            'seclev_submit': 'Submit'
        }
        if token:
            security_data['user_token'] = token
            
        try:
            encoded_sec_data = urllib.parse.urlencode(security_data).encode('utf-8')
            self.opener.open(self.security_url, data=encoded_sec_data)
        except Exception as e:
            print(f"[!] Error setting security level: {e}")
            
        return True

    def send_request(self, payload):
        """Sends the SQLi payload to the target page."""
        data = {
            'id': payload,
            'Submit': 'Submit'
        }
        
        try:
            encoded_data = urllib.parse.urlencode(data).encode('utf-8')
            with self.opener.open(self.injection_url, data=encoded_data) as response:
                content_bytes = response.read()
                content_text = content_bytes.decode('utf-8', errors='ignore')
                return {
                    "text": content_text,
                    "status": response.getcode(),
                    "size": len(content_bytes),
                    "word_count": len(content_text.split()),
                    "headers": dict(response.info())
                }
        except Exception as e:
            return {
                "text": f"Connection Error: {e}",
                "status": 500,
                "size": 0,
                "word_count": 0,
                "headers": {}
            }
