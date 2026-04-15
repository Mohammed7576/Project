import requests
from bs4 import BeautifulSoup
import time

class HTTPClient:
    def __init__(self, base_url="http://localhost/"):
        self.base_url = base_url.rstrip('/') + '/'
        self.session = requests.Session()
        self.login_url = f"{self.base_url}login.php"
        self.security_url = f"{self.base_url}security.php"
        self.injection_url = f"{self.base_url}vulnerabilities/sqli/"

    def _get_token(self, url):
        """Extracts user_token from the specified page."""
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            token_input = soup.find('input', {'name': 'user_token'})
            return token_input['value'] if token_input else None
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
        res = self.session.post(self.login_url, data=login_data)
        
        if "Login failed" in res.text:
            print("[!] Login failed. Check credentials.")
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
            
        self.session.post(self.security_url, data=security_data)
        return True

    def send_request(self, payload):
        """Sends the SQLi payload to the target page."""
        # DVWA Medium SQLi uses POST
        data = {
            'id': payload,
            'Submit': 'Submit'
        }
        
        try:
            # Note: In DVWA Medium, the injection is often via POST on the SQLi page
            response = self.session.post(self.injection_url, data=data)
            return {
                "text": response.text,
                "status": response.status_code,
                "headers": dict(response.headers)
            }
        except Exception as e:
            return {
                "text": f"Connection Error: {e}",
                "status": 500,
                "headers": {}
            }
