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
        self.security_level = security_level.lower()
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

    def fetch_base_payloads(self):
        """Fetches seeded payloads from the server's database API."""
        try:
            # The Prometheus server is at localhost:3000
            res = requests.get("http://localhost:3000/api/base-payloads", timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"[!] Warning: Could not fetch base payloads from DB: {e}")
        return []

    def semantic_search(self, payload, k=5):
        """Fetches semantically similar payloads using the Vector Database API."""
        try:
            # Note: The actual embedding must be provided by the server/frontend.
            # Here we just pass the text and let the server handle the embedding if possible,
            # but our server API expects the embedding. 
            # In AI Studio, we can't easily generate embeddings in Python without heavy libs.
            # So we rely on the server having a 'search-by-text' which first embeds then searches.
            # Let's add that to server.ts
            res = requests.post("http://localhost:3000/api/semantic/search-text", json={"content": payload, "k": k}, timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            pass
        return []

    def send_request(self, payload):
        """Sends the SQLi payload to the target page."""
        params = {
            'id': payload,
            'Submit': 'Submit'
        }
        
        try:
            # Dynamic method switching based on DVWA security context
            if getattr(self, 'security_level', 'medium') == 'low':
                # DVWA Low uses GET parameters
                response = self.session.get(self.injection_url, params=params)
            else:
                # DVWA Medium uses POST body
                response = self.session.post(self.injection_url, data=params)
                
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
