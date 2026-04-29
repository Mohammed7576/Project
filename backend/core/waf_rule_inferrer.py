import re
from collections import Counter

class WAFRuleInferrer:
    """
    Analyzes batches of blocked payloads to infer minimal WAF signatures.
    Instead of analyzing one at a time, it looks for common patterns across multiple failures.
    """
    def __init__(self, semantic_memory=None):
        self.semantic_memory = semantic_memory
        self.min_occurrence = 3 # Minimum failures to consider it a "rule"
        self.inferred_rules = []

    def _tokenize(self, text):
        """SQL-aware tokenizer."""
        # Normalize: replace numbers with placeholders, strip whitespace
        normalized = re.sub(r'\d+', '?', text.upper())
        tokens = re.findall(r"[\w']+|[^\w\s]", normalized)
        return [t for t in tokens if t.strip()]

    def analyze_batch(self, blocked_payloads):
        """
        Analyzes a batch of blocked payloads to find overlapping n-grams.
        Uses a sliding window approach across the entire batch.
        """
        if not blocked_payloads or len(blocked_payloads) < self.min_occurrence:
            return []

        all_ngrams = []
        for payload in blocked_payloads:
            tokens = self._tokenize(payload)
            # Generate n-grams (2 to 5 tokens)
            for n in range(2, 6):
                for i in range(len(tokens) - n + 1):
                    ngram = " ".join(tokens[i:i+n])
                    all_ngrams.append(ngram)

        # Count frequencies
        counts = Counter(all_ngrams)
        new_rules = []
        
        # Filter by significance
        # A pattern is significant if it appears in a high % of the blocked batch
        threshold = max(self.min_occurrence, len(blocked_payloads) * 0.4)
        
        for ngram, count in counts.items():
            if count >= threshold:
                # Potential candidate. Now check if it's too generic
                # (e.g., "SELECT" is too generic, but "SELECT FROM INFORMATION_SCHEMA" is good)
                if len(ngram.split()) >= 2:
                    new_rules.append({
                        "pattern": ngram,
                        "confidence": count / len(blocked_payloads),
                        "frequency": count
                    })

        # Sort by confidence and length (longer specific patterns first)
        new_rules.sort(key=lambda x: (x['confidence'], len(x['pattern'])), reverse=True)
        
        # Deduplicate refined patterns (remove "A B" if "A B C" is also a rule with similar confidence)
        refined = []
        for rule in new_rules:
            is_redundant = False
            for other in refined:
                if rule['pattern'] in other['pattern'] and abs(rule['confidence'] - other['confidence']) < 0.1:
                    is_redundant = True
                    break
            if not is_redundant:
                refined.append(rule)
                if self.semantic_memory:
                    self.semantic_memory.insert_pattern(rule['pattern'], rule['confidence'])

        self.inferred_rules = refined
        return refined

    def get_blocking_reason(self, payload):
        """Analyzes a single payload against inferred rules to explain 'why' it was blocked."""
        matches = []
        normalized = " ".join(self._tokenize(payload))
        for rule in self.inferred_rules:
            if rule['pattern'] in normalized:
                matches.append(rule)
        return matches
