import aiohttp
import asyncio
from bs4 import BeautifulSoup
import time
import json

class HTTPClient:
    def __init__(self, base_url="http://localhost/"):
        self.base_url = base_url.rstrip('/') + '/'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Guard against base_url being a specific file
        if "login.php" in self.base_url:
            self.base_url = self.base_url.replace("login.php", "").rstrip('/') + '/'

        self.login_url = f"{self.base_url}login.php"
        self.security_url = f"{self.base_url}security.php"
        self.injection_url = f"{self.base_url}vulnerabilities/sqli/"
        self.session = None
        self.security_level = "medium"

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _get_token(self, url):
        """Extracts user_token from the specified page."""
        try:
            async with self.session.get(url, timeout=5) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                token_input = soup.find('input', {'name': 'user_token'})
                return token_input['value'] if token_input else None
        except Exception as e:
            self.log(f"[!] Error extracting CSRF token: {e}")
            return None

    def log(self, message, type="log"):
        """Sends a message that the server will broadcast via WebSocket."""
        print(json.dumps({"type": type, "message": message}), flush=True)

    async def setup_dvwa(self, username="admin", password="password", security_level="medium"):
        """Performs login and sets security level."""
        self.security_level = security_level.lower()
        self.log(f"[*] Initializing connection to {self.base_url}...")
        
        # 1. Login
        token = await self._get_token(self.login_url)
        login_data = {
            'username': username,
            'password': password,
            'Login': 'Login'
        }
        if token:
            login_data['user_token'] = token
            
        self.log(f"[*] Attempting login as '{username}'...")
        async with self.session.post(self.login_url, data=login_data, timeout=10) as res:
            text = await res.text()
            if "Login failed" in text:
                self.log("[!] Login failed. Check credentials.")
                return False
            
        # 2. Set Security Level
        self.log(f"[*] Setting Security Level to: {security_level.upper()}")
        token = await self._get_token(self.security_url)
        security_data = {
            'security': security_level.lower(),
            'seclev_submit': 'Submit'
        }
        if token:
            security_data['user_token'] = token
            
        async with self.session.post(self.security_url, data=security_data, timeout=5):
            pass
            
        return True

    async def fetch_base_payloads(self):
        """Fetches seeded payloads from the server's database API."""
        try:
            async with self.session.get("http://localhost:3000/api/base-payloads", timeout=5) as res:
                if res.status == 200:
                    return await res.json()
        except Exception as e:
            self.log(f"[!] Warning: Could not fetch base payloads from DB: {e}")
        return []

    async def semantic_search(self, payload, k=5):
        """Fetches semantically similar payloads using the Vector Database API."""
        try:
            async with self.session.post("http://localhost:3000/api/semantic/search-text", 
                                        json={"content": payload, "k": k}, timeout=5) as res:
                if res.status == 200:
                    return await res.json()
        except Exception as e:
            pass
        return []

    async def send_request(self, payload):
        """Sends the SQLi payload to the target page and measures latency."""
        params = {
            'id': payload,
            'Submit': 'Submit'
        }
        
        start_time = time.time()
        try:
            # Dynamic method switching based on DVWA security context
            if self.security_level == 'low':
                # DVWA Low uses GET parameters
                async with self.session.get(self.injection_url, params=params, timeout=10) as response:
                    text = await response.text()
                    status = response.status
                    headers = dict(response.headers)
            else:
                # DVWA Medium uses POST body
                async with self.session.post(self.injection_url, data=params, timeout=10) as response:
                    text = await response.text()
                    status = response.status
                    headers = dict(response.headers)
                
            latency = int((time.time() - start_time) * 1000)
            return {
                "text": text,
                "status": status,
                "headers": headers,
                "latency": latency
            }
        except Exception as e:
            return {
                "text": f"Connection Error: {e}",
                "status": 500,
                "headers": {},
                "latency": 0
            }
