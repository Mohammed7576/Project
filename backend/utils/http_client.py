import asyncio
import requests
import time
import json
import random
import re

class HTTPClient:
    """
    Asynchronous HTTP Client using requests wrapped in threads to avoid aiohttp dependency.
    Provides the same async interface while using pre-installed libraries.
    """
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
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.security_level = "medium"

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def log(self, message, type="log"):
        """Sends a message that the server will broadcast via WebSocket."""
        if isinstance(message, dict):
            # If it's already a dict, merge with type if not present or just print it
            if "type" not in message:
                message["type"] = type
            print(json.dumps(message), flush=True)
        else:
            print(json.dumps({"type": type, "message": str(message)}), flush=True)

    async def semantic_search(self, payload, k=5):
        """Fetches semantically similar payloads using the Vector Database API."""
        def _fetch():
            try:
                res = requests.post("http://localhost:3000/api/semantic/search-text", 
                                    json={"content": payload, "k": k}, timeout=5)
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                pass
            return []
        return await asyncio.to_thread(_fetch)

    async def _get_token(self, url):
        """Extracts user_token from the specified page using regex to avoid bs4 dependency."""
        def _fetch():
            try:
                resp = self.session.get(url, timeout=5)
                # Simple regex for user_token
                token_match = re.search(r"name='user_token' value='(.*?)'", resp.text)
                return token_match.group(1) if token_match else None
            except Exception as e:
                self.log(f"[!] Error extracting CSRF token: {e}")
                return None
        return await asyncio.to_thread(_fetch)

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
        
        def _login():
            try:
                res = self.session.post(self.login_url, data=login_data, timeout=10)
                if "Login failed" in res.text:
                    self.log("[!] Login failed. Check credentials.")
                    return False
                return True
            except Exception as e:
                self.log(f"[!] Login error: {e}")
                return False

        if not await asyncio.to_thread(_login):
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
            
        await asyncio.to_thread(lambda: self.session.post(self.security_url, data=security_data, timeout=5))
        return True

    async def fetch_base_payloads(self):
        """Fetches seeded payloads from the server's database API."""
        def _fetch():
            try:
                res = requests.get("http://localhost:3000/api/base-payloads", timeout=5)
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                self.log(f"[!] Warning: Could not fetch base payloads from DB: {e}")
            return []
        return await asyncio.to_thread(_fetch)

    async def send_request(self, payload):
        """Sends the SQLi payload to the target page and measures latency."""
        params = {
            'id': payload,
            'Submit': 'Submit'
        }
        
        def _request():
            start_time = time.time()
            try:
                # Dynamic method switching based on DVWA security context
                if self.security_level == 'low':
                    resp = self.session.get(self.injection_url, params=params, timeout=10)
                else:
                    resp = self.session.post(self.injection_url, data=params, timeout=10)
                    
                latency = int((time.time() - start_time) * 1000)
                return {
                    "text": resp.text,
                    "status": resp.status_code,
                    "headers": dict(resp.headers),
                    "latency": latency
                }
            except Exception as e:
                return {
                    "text": f"Connection Error: {e}",
                    "status": 500,
                    "headers": {},
                    "latency": 0
                }
        return await asyncio.to_thread(_request)
