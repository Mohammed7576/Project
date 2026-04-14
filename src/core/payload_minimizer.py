import re
import time

class PayloadMinimizer:
    def __init__(self, client, validator):
        self.client = client
        self.validator = validator

    def minimize(self, payload, original_score):
        """
        Tries to reduce the payload to its simplest form while maintaining the success score.
        """
        print(f"  [Minimizer] Starting minimization for: {payload[:30]}...", flush=True)
        current_payload = payload
        
        # 1. Remove unnecessary comments
        # Matches /**/ or /*...*/
        comments = re.findall(r'/\*.*?\*/', current_payload)
        for comment in comments:
            test_payload = current_payload.replace(comment, '', 1)
            if self._verify(test_payload, original_score):
                current_payload = test_payload
                print(f"  [Minimizer] Removed comment: {comment}", flush=True)

        # 2. Try to revert case toggling (convert to upper or lower)
        # This is more of a cleanup than a reduction
        test_payload = current_payload.upper()
        if self._verify(test_payload, original_score):
            current_payload = test_payload
        else:
            test_payload = current_payload.lower()
            if self._verify(test_payload, original_score):
                current_payload = test_payload

        # 3. Remove junk/padding characters
        # This is tricky, but we can try removing characters one by one if they are not alphanumeric or SQL keywords
        # For now, let's focus on common junk patterns
        junk_patterns = [r'\s+', r'\+', r'%20', r'%0A', r'%09']
        for pattern in junk_patterns:
            parts = re.split(f'({pattern})', current_payload)
            if len(parts) > 1:
                for i in range(1, len(parts), 2):
                    # Try replacing the separator with a single space
                    test_parts = list(parts)
                    test_parts[i] = ' '
                    test_payload = "".join(test_parts)
                    if self._verify(test_payload, original_score):
                        current_payload = test_payload

        print(f"  [Minimizer] Final minimized payload: {current_payload}", flush=True)
        return current_payload

    def _verify(self, payload, target_score):
        try:
            response = self.client.send_request(payload)
            score, _ = self.validator.validate(response['text'], response['status'])
            return score >= target_score
        except Exception:
            return False
