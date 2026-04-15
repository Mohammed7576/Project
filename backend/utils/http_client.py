import requests
from bs4 import BeautifulSoup

class HTTPClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.user_token = None

    def setup_dvwa(self, username, password, security_level):
        try:
            # Get initial token
            login_url = f"{self.base_url}/login.php"
            r = self.session.get(login_url)
            soup = BeautifulSoup(r.text, 'html.parser')
            token_input = soup.find('input', {'name': 'user_token'})
            if not token_input:
                return False
            self.user_token = token_input['value']

            # Login
            data = {
                'username': username,
                'password': password,
                'Login': 'Login',
                'user_token': self.user_token
            }
            r = self.session.post(login_url, data=data)
            if 'Welcome' not in r.text and 'dvwa' not in r.url.lower():
                pass # sometimes it redirects

            # Set security level
            security_url = f"{self.base_url}/security.php"
            r = self.session.get(security_url)
            soup = BeautifulSoup(r.text, 'html.parser')
            token_input = soup.find('input', {'name': 'user_token'})
            if token_input:
                self.user_token = token_input['value']
                data = {
                    'security': security_level,
                    'seclev_submit': 'Submit',
                    'user_token': self.user_token
                }
                self.session.post(security_url, data=data)
            return True
        except Exception as e:
            print(f"Error setting up DVWA: {e}")
            return False

    def send_request(self, payload):
        try:
            url = f"{self.base_url}/vulnerabilities/sqli/"
            params = {'id': payload, 'Submit': 'Submit'}
            r = self.session.get(url, params=params)
            return {'text': r.text, 'status_code': r.status_code, 'url': r.url}
        except Exception as e:
            return {'text': '', 'status_code': 500, 'url': ''}
