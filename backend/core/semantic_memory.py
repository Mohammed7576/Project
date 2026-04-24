import re
import random
import numpy as np
from collections import defaultdict

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.confidence = 0.0

class SemanticMemory:
    """
    Point 1, 2, 3: Semantic Memory implementation.
    Includes Trie for fast lookup, N-Gram analysis for tokens, and similarity search.
    """
    def __init__(self, exp_manager):
        self.exp_manager = exp_manager
        self.root = TrieNode()
        self.token_reputation = {} # Local cache
        self.blocked_patterns = [] # For similarity search
        self._load_memory()

    def _load_memory(self):
        """Loads known blocking patterns and tokens from DB."""
        try:
            conn = self.exp_manager.conn
            cursor = conn.cursor()
            
            # Load Patterns into Trie
            cursor.execute("SELECT pattern, confidence FROM blocking_rules")
            for row in cursor.fetchall():
                self.insert_pattern(row[0], row[1])
            
            # Load Token Reputation
            cursor.execute("SELECT token, reputation FROM token_reputation")
            for row in cursor.fetchall():
                self.token_reputation[row[0]] = row[1]
                
            # Load Sampled Blocked Payloads for Similarity
            cursor.execute("SELECT payload FROM experience WHERE status = 'WAF_BLOCKED' LIMIT 100")
            self.blocked_patterns = [r[0] for r in cursor.fetchall()]
        except Exception as e:
            print(f"[!] Semantic Memory Load Error: {e}")

    def insert_pattern(self, pattern, confidence=1.0):
        """Inserts a blocked pattern into the Trie."""
        node = self.root
        tokens = self._tokenize(pattern)
        for token in tokens:
            if token not in node.children:
                node.children[token] = TrieNode()
            node = node.children[token]
        node.is_end = True
        node.confidence = confidence

    def check_payload(self, payload):
        """
        Point 3: Fast Trie Lookup.
        Returns (is_blocked, confidence, matched_pattern).
        """
        tokens = self._tokenize(payload)
        # Check every sliding window of tokens in the trie
        for i in range(len(tokens)):
            node = self.root
            for j in range(i, len(tokens)):
                if tokens[j] not in node.children:
                    break
                node = node.children[tokens[j]]
                if node.is_end:
                    return True, node.confidence, " ".join(tokens[i:j+1])
        
        # Point 1: Similarity Check (Simulated Vector Search)
        # Using a simple Jaccard similarity or Sequence Matcher for now
        for blocked in self.blocked_patterns:
            sim = self._calculate_similarity(payload, blocked)
            if sim > 0.9:
                return True, 0.8, f"Similar to {blocked[:20]}..."
                
        return False, 0.0, None

    def update_reputation(self, payload, is_success):
        """
        Point 2: Token-based Credit Assignment (N-Grams).
        Assigns positive/negative credit to specific words/tokens.
        """
        tokens = self._tokenize(payload)
        delta = 0.05 if is_success else -0.1
        
        # Update 1-Grams (Individual words)
        for token in tokens:
            current = self.token_reputation.get(token, 1.0)
            self.token_reputation[token] = max(0.1, min(2.0, current + delta))
            
        # Point 4: Shared Knowledge Update (Consolidation)
        if random.random() < 0.1: # 10% chance to sync per reported result
            self.sync_to_db()

    def sync_to_db(self):
        """Persists learned token reputations to shared database."""
        try:
            conn = self.exp_manager.conn
            cursor = conn.cursor()
            for token, rep in self.token_reputation.items():
                cursor.execute('''
                    INSERT INTO token_reputation (token, reputation)
                    VALUES (?, ?)
                    ON CONFLICT(token) DO UPDATE SET reputation = excluded.reputation
                ''', (token, rep))
            conn.commit()
        except Exception as e:
            print(f"[!] Semantic Memory Sync Error: {e}")

    def _tokenize(self, text):
        """Splits payload into meaningful SQL tokens."""
        # Split by non-alphanumeric but keep common SQL chars
        tokens = re.findall(r"[\w']+|[^\w\s]", text.upper())
        return [t for t in tokens if t.strip()]

    def _calculate_similarity(self, p1, p2):
        """Simple token-based similarity."""
        s1 = set(self._tokenize(p1))
        s2 = set(self._tokenize(p2))
        if not s1 or not s2: return 0.0
        return len(s1.intersection(s2)) / len(s1.union(s2))
