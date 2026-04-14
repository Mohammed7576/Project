import torch
import torch.nn as nn
import torch.optim as optim
import json
import sqlite3
import os
import random

class SQLiBrainNet(nn.Module):
    """
    Official PyTorch Neural Network Architecture for SQLi Payload Prediction.
    """
    def __init__(self, input_size, hidden_size, output_size):
        super(SQLiBrainNet, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size)
        )

    def forward(self, x):
        return self.network(x)

class DeepQLearningAgent:
    """
    High-Performance Deep Q-Learning Agent powered by PyTorch.
    """
    def __init__(self, actions, db_path="memory.db", learning_rate=0.001):
        self.actions = actions
        self.input_size = 12 # 10 WAF features + score + stagnation
        self.output_size = len(actions)
        self.db_path = db_path
        
        # Initialize PyTorch Model
        self.model = SQLiBrainNet(self.input_size, 32, self.output_size)
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        
        self.gamma = 0.95
        self.epsilon = 0.2
        self.load_weights()

    def _encode_state(self, waf_name, score, stagnation):
        # Feature Engineering: Convert context to numerical tensor
        waf_hash = [0.0] * 10
        for char in waf_name:
            waf_hash[ord(char) % 10] += 0.1
        
        state_list = waf_hash + [float(score), float(stagnation) / 10.0]
        return torch.FloatTensor(state_list).unsqueeze(0) # Add batch dimension

    def choose_action(self, waf_name, score, stagnation):
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        
        state_tensor = self._encode_state(waf_name, score, stagnation)
        
        self.model.eval()
        with torch.no_grad():
            q_values = self.model(state_tensor)
        self.model.train()
        
        action_idx = torch.argmax(q_values).item()
        return self.actions[action_idx]

    def learn(self, waf_name, score, stagnation, action, reward, next_score, next_stagnation):
        state_tensor = self._encode_state(waf_name, score, stagnation)
        next_state_tensor = self._encode_state(waf_name, next_score, next_stagnation)
        
        # Get current Q values
        current_q = self.model(state_tensor)
        
        # Get next Q values for target calculation
        with torch.no_grad():
            next_q = self.model(next_state_tensor)
        
        action_idx = self.actions.index(action)
        
        # Bellman Equation: Target Q = reward + gamma * max(next_q)
        target_q = current_q.clone().detach()
        target_q[0][action_idx] = reward + self.gamma * torch.max(next_q)
        
        # Training Step
        self.optimizer.zero_grad()
        loss = self.criterion(current_q, target_q)
        loss.backward()
        self.optimizer.step()

    def save(self):
        """Saves model state_dict to SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Serialize model weights
            buffer = self.model.state_dict()
            # Convert tensors to lists for JSON serialization (since we are in a DB)
            serializable_weights = {k: v.tolist() for k, v in buffer.items()}
            weights_json = json.dumps(serializable_weights)
            
            cursor.execute("""
                INSERT INTO rl_knowledge (state, actions_json, last_updated)
                VALUES ('PYTORCH_MODEL_WEIGHTS', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(state) DO UPDATE SET
                    actions_json = excluded.actions_json,
                    last_updated = CURRENT_TIMESTAMP
            """, (weights_json,))
            conn.commit()
            conn.close()
            print("[*] PyTorch: Model weights saved to database.")
        except Exception as e:
            print(f"[!] PyTorch: Error saving weights: {e}")

    def load_weights(self):
        """Loads model state_dict from SQLite database."""
        if not os.path.exists(self.db_path): return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT actions_json FROM rl_knowledge WHERE state = 'PYTORCH_MODEL_WEIGHTS'")
            row = cursor.fetchone()
            if row:
                weights_dict = json.loads(row[0])
                # Convert lists back to torch tensors
                state_dict = {k: torch.tensor(v) for k, v in weights_dict.items()}
                self.model.load_state_dict(state_dict)
                print("[*] PyTorch: Neural weights loaded and synchronized.")
            conn.close()
        except Exception as e:
            print(f"[!] PyTorch: Error loading weights: {e}")
