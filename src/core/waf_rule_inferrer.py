import re
import time
import random

class WAFRuleInferrer:
    def __init__(self, client):
        self.client = client
        self.inferred_rules = [] # List of dicts: {"pattern": str, "type": "KEYWORD|SEQUENCE|REGEX", "confidence": float}
        self.knowledge_base = {} # Cache of tested tokens

    def infer(self, blocked_payload):
        """
        Interrogates the WAF by testing variations of the blocked payload to map its rules.
        """
        print(f"  [Inferrer] Interrogating WAF for payload: {blocked_payload[:30]}...", flush=True)
        
        # 1. Tokenize the payload
        tokens = re.findall(r"[\w']+|[^\w\s]", blocked_payload)
        if not tokens: return None

        # 2. Isolate the trigger (Bisection-like)
        trigger = self._isolate_trigger(tokens)
        if not trigger: return None

        print(f"  [Inferrer] Isolated potential trigger: '{trigger}'", flush=True)

        # 3. Test Variations of the trigger to determine rule type
        rule = self._determine_rule_type(trigger)
        if rule:
            self.inferred_rules.append(rule)
            return rule
        
        return None

    def _isolate_trigger(self, tokens):
        """Finds the smallest sequence of tokens that causes a block."""
        # Start with individual tokens
        for token in tokens:
            if token in self.knowledge_base:
                if self.knowledge_base[token] == "BLOCKED": return token
                continue

            if self._is_blocked(token):
                self.knowledge_base[token] = "BLOCKED"
                return token
            else:
                self.knowledge_base[token] = "ALLOWED"

        # If individual tokens are allowed, try pairs (sequences)
        for i in range(len(tokens) - 1):
            pair = f"{tokens[i]} {tokens[i+1]}"
            if self._is_blocked(pair):
                return pair
        
        return None

    def _determine_rule_type(self, trigger):
        """Tests variations to see if it's a simple keyword block or something more complex."""
        # Test Case Sensitivity
        if trigger.isalpha():
            variations = [trigger.lower(), trigger.upper(), trigger.capitalize()]
            results = [self._is_blocked(v) for v in variations]
            if all(results):
                return {"pattern": trigger, "type": "KEYWORD_INSENSITIVE", "confidence": 0.9}
            elif any(results):
                return {"pattern": trigger, "type": "KEYWORD_SENSITIVE", "confidence": 0.8}

        # Test Comment Injection
        if " " in trigger:
            commented = trigger.replace(" ", "/**/")
            if not self._is_blocked(commented):
                return {"pattern": trigger, "type": "SEQUENCE_BYPASSABLE_BY_COMMENTS", "confidence": 0.9}
            
        # Test Encoding
        # (Simplified for now)
        return {"pattern": trigger, "type": "UNKNOWN_BLOCK", "confidence": 0.5}

    def _is_blocked(self, test_string):
        """Sends a minimal request to check if a specific string is blocked."""
        try:
            # We use a very simple context to avoid triggering other rules
            response = self.client.send_request(test_string)
            # If status is 403, 406 or we see WAF markers
            if response['status'] in [403, 406]:
                return True
            # Check for common WAF strings in response
            waf_markers = ["forbidden", "access denied", "waf", "firewall", "security"]
            text = response['text'].lower()
            if any(m in text for m in waf_markers) and response['status'] != 200:
                return True
            return False
        except Exception:
            return True # Assume blocked on error during interrogation
