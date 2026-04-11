import re

class WAFFingerprinter:
    def __init__(self):
        # Signatures for common WAFs
        self.signatures = {
            "Cloudflare": {
                "headers": {"Server": "cloudflare"},
                "body": [r"cf-ray", r"Cloudflare Ray ID"]
            },
            "ModSecurity": {
                "headers": {"Server": "ModSecurity", "X-Powered-By": "ModSecurity"},
                "body": [r"Not Acceptable", r"ModSecurity"]
            },
            "AWS WAF": {
                "headers": {"Server": "AWSALB"},
                "body": [r"x-amzn-RequestId", r"AWSWAF"]
            },
            "Akamai": {
                "headers": {"Server": "AkamaiGHost"},
                "body": [r"Akamai Technologies"]
            },
            "Imperva": {
                "headers": {"X-IWS-ID": ".*", "Server": "imperva"},
                "body": [r"Incapsula incident ID"]
            }
        }

    def identify(self, headers, body):
        """Identifies the WAF based on headers and body."""
        for waf_name, sig in self.signatures.items():
            # Check headers
            for h_name, h_val in sig.get("headers", {}).items():
                actual_val = headers.get(h_name, "")
                if re.search(h_val, actual_val, re.IGNORECASE):
                    return waf_name
            
            # Check body
            for pattern in sig.get("body", []):
                if re.search(pattern, body, re.IGNORECASE):
                    return waf_name
        
        return "GENERIC / UNKNOWN"

    def get_bypass_strategy(self, waf_name):
        """Returns specific mutation strategies for the identified WAF."""
        strategies = {
            "Cloudflare": {
                "weights": {"inline_comments": 3.0, "hex_encoding": 2.0},
                "hint": "Use obfuscated comments and hex encoding for keywords."
            },
            "ModSecurity": {
                "weights": {"junk_fill": 4.0, "logical_alts": 2.0},
                "hint": "Use large junk buffers and alternative logical operators like && instead of AND."
            },
            "Imperva": {
                "weights": {"case_swap": 2.0, "whitespace_variations": 3.0},
                "hint": "Focus on whitespace variations and case manipulation."
            }
        }
        return strategies.get(waf_name, {"weights": {}, "hint": "No specific bypass strategy known. Use generic evolution."})
