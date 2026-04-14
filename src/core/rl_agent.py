import random
import json
import sqlite3
import os

class QLearningAgent:
    def __init__(self, actions, learning_rate=0.2, discount_factor=0.9, epsilon=0.2, db_path="memory.db"):
        self.q_table = {} # State -> {Action: Value}
        self.actions = actions
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.db_path = db_path
        self.state_history = []

    def get_state(self, waf_name, score, stagnation):
        # Discretize score into buckets
        score_bucket = int(score * 10) / 10.0
        # Discretize stagnation
        stag_bucket = min(stagnation, 5)
        return f"{waf_name}|{score_bucket}|{stag_bucket}"

    def choose_action(self, state):
        if state not in self.q_table:
            self.q_table[state] = {a: 1.0 for a in self.actions} # Initial optimism

        # Epsilon-greedy exploration
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        
        # Exploitation: choose best action
        state_actions = self.q_table[state]
        max_val = max(state_actions.values())
        best_actions = [a for a, v in state_actions.items() if v == max_val]
        return random.choice(best_actions)

    def learn(self, state, action, reward, next_state):
        if state not in self.q_table:
            self.q_table[state] = {a: 1.0 for a in self.actions}
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 1.0 for a in self.actions}

        # Q-Learning Formula: Q(s,a) = Q(s,a) + lr * [reward + gamma * max(Q(s',a')) - Q(s,a)]
        old_value = self.q_table[state][action]
        next_max = max(self.q_table[next_state].values())
        
        new_value = old_value + self.lr * (reward + self.gamma * next_max - old_value)
        self.q_table[state][action] = new_value

    def save_knowledge(self):
        """Saves the entire Q-table to the SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for state, actions in self.q_table.items():
                actions_json = json.dumps(actions)
                cursor.execute("""
                    INSERT INTO rl_knowledge (state, actions_json, last_updated)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(state) DO UPDATE SET
                        actions_json = excluded.actions_json,
                        last_updated = CURRENT_TIMESTAMP
                """, (state, actions_json))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Error saving RL knowledge to DB: {e}")

    def load_knowledge(self):
        """Loads all states and actions from the SQLite database into the Q-table."""
        if not os.path.exists(self.db_path):
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT state, actions_json FROM rl_knowledge")
            rows = cursor.fetchall()
            for state, actions_json in rows:
                self.q_table[state] = json.loads(actions_json)
            conn.close()
            if rows:
                print(f"[*] AI Agent: Loaded {len(rows)} states from database knowledge.")
        except Exception as e:
            print(f"[!] Error loading RL knowledge from DB: {e}")
