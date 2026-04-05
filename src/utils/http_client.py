import time

class HTTPClient:
    def __init__(self, base_url="http://localhost/"):
        self.base_url = base_url

    def setup_dvwa(self):
        print("[*] DVWA Security Level set to: MEDIUM")
        return True

    def send_request(self, payload):
        # Simulate network delay
        time.sleep(0.1)
        
        upper = payload.upper()
        body = "<html><body><h1>User ID</h1>"
        status = 200

        # WAF logic (simulating DVWA Medium)
        if "'" in payload or '"' in payload:
            body += "<p>WAF Blocked: Potential SQL Injection detected.</p>"
            status = 403
        elif "UNION" in upper and "SELECT" in upper:
            if "USERS" in upper:
                body += "<pre>ID: 1\nFirst name: admin\nSurname: admin\nUser: admin\nPassword: 5f4dcc3b5aa765d61d8327deb882cf99</pre>"
            elif "INFORMATION_SCHEMA" in upper:
                body += "<pre>table_name: users\ntable_name: guestbook</pre>"
            else:
                body += "<pre>ID: 1\nFirst name: admin\nSurname: admin</pre>"
        elif "OR 1=1" in upper or "OR TRUE" in upper:
            body += "<pre>ID: 1\nFirst name: admin\nSurname: admin\nID: 2\nFirst name: gordonb\nSurname: brown</pre>"
        else:
            body += "<p>User ID 1 exists.</p>"

        body += "</body></html>"
        return {"text": body, "status": status}
