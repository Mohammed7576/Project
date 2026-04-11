import random
import time
from core.mutator_ast import ASTMutator
from utils.success_validator import SuccessValidator

class IslandManager:
    def __init__(self, client, base_payloads, exp_manager, population_size=12):
        self.client = client
        self.exp_manager = exp_manager
        self.base_seeds = base_payloads
        self.population_size = population_size
        self.mutator = ASTMutator()
        self.validator = SuccessValidator()
        self.best_score_history = []
        self.hall_of_fame = [] 
        self.discovered_niches = set() # Awareness: Track types of successes (e.g. UNION, Error)
        self.stagnation_counter = 0
        
        # 1. Experience-Driven Initialization
        golden_seeds = self.exp_manager.get_golden_payloads(limit=4)
        if golden_seeds:
            print(f"[*] Learning from history: Injecting {len(golden_seeds)} golden payloads.", flush=True)
            
        combined_seeds = golden_seeds + base_payloads
        
        if combined_seeds:
            sample_size = min(len(combined_seeds), self.population_size)
            self.population = random.sample(combined_seeds, sample_size)
        else:
            self.population = []

    def _calculate_similarity(self, p1, p2):
        """Simple Jaccard similarity based on characters to detect structural bias."""
        s1, s2 = set(p1), set(p2)
        intersection = len(s1.intersection(s2))
        union = len(s1.union(s2))
        return intersection / union if union > 0 else 0

    def evolve_generation(self, gen_num):
        if not self.population:
            return None

        scored_population = []
        max_gen_score = 0
        success_count = 0
        
        # 1. Stagnation Detection
        if len(self.best_score_history) > 2:
            if self.best_score_history[-1] <= self.best_score_history[-2]:
                self.stagnation_counter += 1
            else:
                self.stagnation_counter = 0

        mutation_intensity = 1
        if self.stagnation_counter >= 3:
            mutation_intensity = 3 
            print(f"[!] Stagnation detected. Injecting chaos (Intensity: {mutation_intensity})...", flush=True)

        for i, payload in enumerate(self.population):
            # Skip exact matches in Hall of Fame
            if payload in self.hall_of_fame:
                continue

            response = self.client.send_request(payload)
            score, status = self.validator.validate(response['text'], response['status'])
            
            # 2. Similarity Penalty: Avoid Bias
            # If this payload is too similar to something we already solved, penalize its score
            # to encourage exploring different structures.
            for successful_p in self.hall_of_fame:
                if self._calculate_similarity(payload, successful_p) > 0.8:
                    score *= 0.5
                    status = f"BIASED_{status}"
                    break

            if score >= 0.5: success_count += 1
            
            error_msg = self.validator.get_sql_error(response['text'])
            
            print(f"  [>] Testing {i+1}/{len(self.population)}: {payload[:40]}... [Score: {score:.2f} | {status}]", flush=True)
            
            self.exp_manager.save_attempt(payload, score, status)
            self.mutator.report_success(score)
            scored_population.append((payload, score, error_msg))
            
            if score > max_gen_score:
                max_gen_score = score
            
            # 3. Multi-Success & Niche Awareness
            if score >= 0.9 and payload not in self.hall_of_fame:
                # Check if this is a new "Niche" (new status)
                if status not in self.discovered_niches:
                    print(f"[!!!] NEW EXPLOIT TYPE DISCOVERED ({status}): {payload}", flush=True)
                    self.discovered_niches.add(status)
                    self.hall_of_fame.append(payload)
                    self.exp_manager.save_exploit(payload, status)
                elif score >= 1.0:
                    # Even if niche is known, keep perfect payloads
                    self.hall_of_fame.append(payload)
                    self.exp_manager.save_exploit(payload, "PERFECT_MATCH")

        # 4. Diversity Check
        unique_payloads = len(set(self.population))
        diversity_ratio = unique_payloads / len(self.population)
        if diversity_ratio < 0.4:
            print(f"[*] Critical low diversity ({int(diversity_ratio*100)}%). Purging 50% of population.", flush=True)
            # Keep only top 2, replace rest with fresh seeds
            scored_population.sort(key=lambda x: x[1], reverse=True)
            top_survivors = [p[0] for p in scored_population[:2]]
            fresh_seeds = random.sample(self.base_seeds, min(len(self.base_seeds), self.population_size - 2))
            self.population = top_survivors + fresh_seeds
            self.stagnation_counter = 0 # Reset after purge
            return self.hall_of_fame[-1] if self.hall_of_fame else None

        self.best_score_history.append(max_gen_score)
        scored_population.sort(key=lambda x: x[1], reverse=True)
        
        # Elitism
        elite_count = max(2, int(self.population_size * 0.2))
        elites = [p[0] for p in scored_population[:elite_count]]
        
        # Survivors
        survivors = [p for p in scored_population if p[1] >= 0.15] # Lowered threshold to keep more genetic material
        
        self.population = self._generate_next_gen(elites, survivors, mutation_intensity)
        
        return self.hall_of_fame[-1] if self.hall_of_fame else None

    def _generate_next_gen(self, elites, survivors, intensity):
        next_gen = list(elites) # Start with elites
        
        if not survivors:
            return random.sample(self.base_seeds, min(len(self.base_seeds), self.population_size))

        while len(next_gen) < self.population_size:
            rand_val = random.random()
            
            if rand_val < 0.1: # 10% Chance of fresh seed
                next_gen.append(random.choice(self.base_seeds))
            elif rand_val < 0.4 and len(survivors) >= 2: # 30% Crossover
                p1, p2 = random.sample(survivors, 2)
                child = self._crossover(p1[0], p2[0])
                next_gen.append(self.mutator.mutate(child, intensity=intensity))
            else: # 60% Mutation
                parent_data = random.choice(survivors)
                parent_payload = parent_data[0]
                error_feedback = parent_data[2]
                
                # Context-Aware & Error-Based Mutation
                child = self.mutator.mutate(parent_payload, error_msg=error_feedback, intensity=intensity)
                if child not in next_gen:
                    next_gen.append(child)
        
        return next_gen

    def _crossover(self, p1, p2):
        """Combines two payloads by splitting them at a random keyword."""
        keywords = ["UNION", "SELECT", "WHERE", "AND", "OR"]
        for kw in keywords:
            if kw in p1.upper() and kw in p2.upper():
                parts1 = p1.upper().split(kw)
                parts2 = p2.upper().split(kw)
                return parts1[0] + kw + parts2[1]
        # Fallback: simple string split
        split_idx = len(p1) // 2
        return p1[:split_idx] + p2[split_idx:]
