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

    def probe(self, client):
        """Sends specific characters to see what's blocked by the WAF."""
        probes = {
            "single_quote": "'",
            "space": " ",
            "union": "UNION",
            "comment": "--",
            "bracket": "(",
            "semicolon": ";"
        }
        blocked = []
        print("[*] WAF Fingerprinter: Probing for blocked characters...", flush=True)
        for name, char in probes.items():
            try:
                response = client.send_request(char)
                if response['status'] in [403, 406, 429]:
                    blocked.append(char)
            except:
                pass
        return blocked

    def get_bypass_strategy(self, waf_name, blocked_chars=None):
        """Returns specific mutation strategies for the identified WAF."""
        strategies = {
            "Cloudflare": {
                "weights": {"inline_comments": 4.0, "directed_bypass": 3.0},
                "hint": "Cloudflare detected. Prioritizing inline comments and directed keyword bypasses."
            },
            "ModSecurity": {
                "weights": {"junk_fill": 5.0, "logical_alts": 3.0},
                "hint": "ModSecurity detected. Using large junk buffers and alternative logical operators."
            },
            "AWS WAF": {
                "weights": {"context_aware": 4.0, "union_balance": 2.0},
                "hint": "AWS WAF detected. Focusing on context-aware wrapping and union balancing."
            },
            "Imperva": {
                "weights": {"directed_bypass": 4.0, "inline_comments": 2.0},
                "hint": "Imperva detected. Using directed bypasses for sensitive keywords."
            }
        }
        
        strategy = strategies.get(waf_name, {"weights": {}, "hint": "Generic WAF or unknown. Using standard evolution."})
        
        # Adjust strategy based on blocked characters
        if blocked_chars:
            if " " in blocked_chars:
                strategy["weights"]["context_aware"] = strategy["weights"].get("context_aware", 1.0) * 3.0
                strategy["hint"] += " Space character is blocked. Using alternative separators."
            if "UNION" in blocked_chars:
                strategy["weights"]["directed_bypass"] = strategy["weights"].get("directed_bypass", 1.0) * 4.0
                strategy["hint"] += " UNION keyword is blocked. Applying heavy obfuscation."
                
        return strategy
