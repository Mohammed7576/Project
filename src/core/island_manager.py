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
        
        if base_payloads:
            sample_size = min(len(base_payloads), self.population_size)
            self.population = random.sample(base_payloads, sample_size)
        else:
            self.population = []

    def evolve_generation(self, gen_num):
        if not self.population:
            if self.base_seeds:
                self.population = random.sample(self.base_seeds, min(len(self.base_seeds), self.population_size))
            else:
                return None

        scored_population = []
        for i, payload in enumerate(self.population):
            # Simulate request
            response = self.client.send_request(payload)
            score, status = self.validator.validate(response['text'], response['status'])
            
            print(f"  [>] Testing {i+1}/{len(self.population)}: {payload[:40]}... [Score: {score} | {status}]", flush=True)
            
            self.exp_manager.save_attempt(payload, score, status)
            scored_population.append((payload, score))
            
            if score >= 1.0:
                return payload

        scored_population.sort(key=lambda x: x[1], reverse=True)
        survivors = [p[0] for p in scored_population if p[1] >= 0.4]
        
        self.population = self._generate_next_gen(survivors)
        return None

    def _generate_next_gen(self, survivors):
        next_gen = []
        if not survivors:
            return random.sample(self.base_seeds, min(len(self.base_seeds), self.population_size))

        next_gen.append(survivors[0]) # Elitism
        
        while len(next_gen) < self.population_size:
            if random.random() < 0.3:
                next_gen.append(random.choice(self.base_seeds))
            else:
                parent = random.choice(survivors)
                child = self.mutator.mutate(parent)
                if child not in next_gen:
                    next_gen.append(child)
        
        return next_gen
