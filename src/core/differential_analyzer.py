import re
import time

class DifferentialAnalyzer:
    def __init__(self, client):
        self.client = client
        self.known_signatures = set()

    def analyze(self, payload):
        """
        Performs binary search on a blocked payload to find the exact WAF signature.
        Returns the specific substring that triggers the block.
        """
        # Clean payload a bit to avoid splitting half-encoded chars
        if len(payload) < 5:
            return None
            
        print(f"  [Diff-Analyzer] Isolating WAF signature in: {payload[:20]}...", flush=True)
        signature = self._binary_search(payload)
        
        if signature and len(signature) >= 3 and signature != payload:
            self.known_signatures.add(signature)
            print(f"  [!!!] WAF Signature Isolated: '{signature}'", flush=True)
            return signature
        return None

    def _binary_search(self, text):
        if len(text) <= 4:
            return text

        mid = len(text) // 2
        left = text[:mid]
        right = text[mid:]

        if self._is_blocked(left):
            return self._binary_search(left)
        
        if self._is_blocked(right):
            return self._binary_search(right)

        # If neither is blocked, the signature crosses the boundary.
        # We return the whole text as the minimal bounding box for the signature.
        return text

    def _is_blocked(self, payload):
        try:
            response = self.client.send_request(payload)
            if response['status'] in [403, 406, 501]:
                return True
            waf_keywords = ["blocked", "forbidden", "waf", "security policy", "not acceptable", "firewall"]
            if any(kw in response['text'].lower() for kw in waf_keywords):
                return True
            return False
        except Exception:
            return False
