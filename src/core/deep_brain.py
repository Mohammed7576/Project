import torch
import torch.nn as nn
import torch.optim as optim
import json
import sqlite3
import os
import random
import math
from collections import deque

class SQLiBrainLSTM(nn.Module):
    """
    Advanced PyTorch LSTM Architecture for Sequential SQLi Payload Prediction.
    Adds Temporal Awareness to understand compound strategies.
    """
    def __init__(self, input_size, hidden_size, output_size):
        super(SQLiBrainLSTM, self).__init__()
        self.hidden_size = hidden_size
        # LSTM Layer (batch_first=True expects input shape: [batch, seq_len, features])
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc1 = nn.Linear(hidden_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        # If input is 2D (batch, features), add a sequence dimension (batch, 1, features)
        if x.dim() == 2:
            x = x.unsqueeze(1)
            
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # Extract the output of the last time step
        out = lstm_out[:, -1, :]
        out = self.relu(self.fc1(out))
        out = self.fc2(out)
        return out

class DeepQLearningAgent:
    """
    High-Performance Deep Q-Learning Agent powered by PyTorch with Experience Replay.
    """
    def __init__(self, actions, exp_manager, db_path="memory.db", learning_rate=0.001):
        self.actions = actions
        self.exp_manager = exp_manager
        self.input_size = 16 # 10 WAF + score + stagnation + 4 payload features
        self.output_size = len(actions)
        self.db_path = db_path
        
        # Initialize PyTorch LSTM Model
        self.model = SQLiBrainLSTM(self.input_size, 32, self.output_size)
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        
        self.gamma = 0.95
        # Dynamic Epsilon (Decaying Exploration)
        self.epsilon_start = 0.9
        self.epsilon_end = 0.05
        self.epsilon_decay = 1000
        self.steps_done = 0
        self.epsilon = self.epsilon_start
        
        # Experience Replay Buffer
        self.memory = deque(maxlen=5000)
        self.batch_size = 16
        
        self.load_weights()

    def _encode_state(self, waf_name, score, stagnation, payload):
        # Feature Engineering: Convert context to numerical tensor
        waf_hash = [0.0] * 10
        for char in waf_name:
            waf_hash[ord(char) % 10] += 0.1
            
        # Payload Deep Embeddings
        payload_str = str(payload)
        len_feat = min(len(payload_str) / 200.0, 1.0)
        kw_feat = sum(payload_str.upper().count(kw) for kw in ["UNION", "SELECT", "AND", "OR", "WHERE"]) / 10.0
        sp_feat = sum(payload_str.count(c) for c in ["'", '"', "*", "/", "-", "#"]) / 20.0
        enc_feat = 1.0 if "%" in payload_str or "0x" in payload_str.lower() else 0.0
        
        state_list = waf_hash + [float(score), float(stagnation) / 10.0, len_feat, kw_feat, sp_feat, enc_feat]
        return torch.FloatTensor(state_list).unsqueeze(0) # Add batch dimension

    def choose_action(self, waf_name, score, stagnation, payload):
        # Calculate dynamic epsilon
        self.epsilon = self.epsilon_end + (self.epsilon_start - self.epsilon_end) * \
            math.exp(-1. * self.steps_done / self.epsilon_decay)
        self.steps_done += 1

        if random.random() < self.epsilon:
            action = random.choice(self.actions)
            self.exp_manager.log_brain_activity("CURIOSITY", f"Exploring randomly. Epsilon: {self.epsilon:.2f}. Chose: {action}", self.epsilon)
            return action
        
        state_tensor = self._encode_state(waf_name, score, stagnation, payload)
        
        self.model.eval()
        with torch.no_grad():
            q_values = self.model(state_tensor)
        self.model.train()
        
        action_idx = torch.argmax(q_values).item()
        action = self.actions[action_idx]
        confidence = float(torch.max(torch.softmax(q_values, dim=1)).item())
        self.exp_manager.log_brain_activity("DECISION", f"Exploiting knowledge. Chose: {action}", confidence)
        return action

    def remember(self, state, action, reward, next_state):
        """Stores experience in the replay buffer."""
        self.memory.append((state, action, reward, next_state))

    def replay(self):
        """Trains the neural network using a random batch from the replay buffer."""
        if len(self.memory) < self.batch_size:
            return # Not enough memories to train yet
            
        # Sample a random batch of memories
        batch = random.sample(self.memory, self.batch_size)
        
        # Vectorized preparation for PyTorch
        state_batch = torch.cat([b[0] for b in batch])
        action_batch = [self.actions.index(b[1]) for b in batch]
        reward_batch = torch.FloatTensor([b[2] for b in batch])
        next_state_batch = torch.cat([b[3] for b in batch])
        
        # Current Q Values
        current_q = self.model(state_batch)
        
        # Next Q Values (Target Network logic)
        with torch.no_grad():
            next_q = self.model(next_state_batch)
            
        # Bellman Equation: Target Q = reward + gamma * max(next_q)
        target_q = current_q.clone().detach()
        for i in range(self.batch_size):
            target_q[i][action_batch[i]] = reward_batch[i] + self.gamma * torch.max(next_q[i])
            
        # Training Step
        self.optimizer.zero_grad()
        loss = self.criterion(current_q, target_q)
        loss.backward()
        self.optimizer.step()

    def learn(self, waf_name, score, stagnation, payload, action, reward, next_score, next_stagnation, next_payload):
        state_tensor = self._encode_state(waf_name, score, stagnation, payload)
        next_state_tensor = self._encode_state(waf_name, next_score, next_stagnation, next_payload)
        
        # 1. Store the experience in memory
        self.remember(state_tensor, action, reward, next_state_tensor)
        
        # 2. Train the network using a batch of past experiences
        self.replay()

    def save(self):
        """Saves model state_dict and replay buffer to SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Serialize model weights
            buffer = self.model.state_dict()
            serializable_weights = {k: v.tolist() for k, v in buffer.items()}
            weights_json = json.dumps(serializable_weights)
            
            # Serialize Replay Buffer (limit to last 1000 to save DB space)
            memory_list = []
            for s, a, r, ns in list(self.memory)[-1000:]:
                memory_list.append({"s": s.tolist(), "a": a, "r": r, "ns": ns.tolist()})
            memory_json = json.dumps(memory_list)
            
            # Save Weights
            cursor.execute("""
                INSERT INTO rl_knowledge (state, actions_json, last_updated)
                VALUES ('PYTORCH_MODEL_WEIGHTS_V3_LSTM', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(state) DO UPDATE SET
                    actions_json = excluded.actions_json,
                    last_updated = CURRENT_TIMESTAMP
            """, (weights_json,))
            
            # Save Replay Buffer
            cursor.execute("""
                INSERT INTO rl_knowledge (state, actions_json, last_updated)
                VALUES ('PYTORCH_REPLAY_BUFFER_V3_LSTM', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(state) DO UPDATE SET
                    actions_json = excluded.actions_json,
                    last_updated = CURRENT_TIMESTAMP
            """, (memory_json,))
            
            # Save Epsilon State
            cursor.execute("""
                INSERT INTO rl_knowledge (state, actions_json, last_updated)
                VALUES ('PYTORCH_EPSILON_STATE_V3_LSTM', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(state) DO UPDATE SET
                    actions_json = excluded.actions_json,
                    last_updated = CURRENT_TIMESTAMP
            """, (json.dumps({"steps_done": self.steps_done}),))
            
            conn.commit()
            conn.close()
            print("[*] PyTorch: Model weights & Replay Buffer saved to database.")
        except Exception as e:
            print(f"[!] PyTorch: Error saving weights: {e}")

    def load_weights(self):
        """Loads model state_dict and replay buffer from SQLite database."""
        if not os.path.exists(self.db_path): return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load Weights
            cursor.execute("SELECT actions_json FROM rl_knowledge WHERE state = 'PYTORCH_MODEL_WEIGHTS_V3_LSTM'")
            row = cursor.fetchone()
            if row:
                weights_dict = json.loads(row[0])
                state_dict = {k: torch.tensor(v) for k, v in weights_dict.items()}
                self.model.load_state_dict(state_dict)
                print("[*] PyTorch: Neural weights (V3 LSTM) loaded and synchronized.")
                
            # Load Replay Buffer
            cursor.execute("SELECT actions_json FROM rl_knowledge WHERE state = 'PYTORCH_REPLAY_BUFFER_V3_LSTM'")
            row_mem = cursor.fetchone()
            if row_mem:
                memory_list = json.loads(row_mem[0])
                for item in memory_list:
                    self.memory.append((
                        torch.FloatTensor(item["s"]),
                        item["a"],
                        item["r"],
                        torch.FloatTensor(item["ns"])
                    ))
                print(f"[*] PyTorch: Restored {len(self.memory)} memories to Replay Buffer (V3 LSTM).")
                
            # Load Epsilon State
            cursor.execute("SELECT actions_json FROM rl_knowledge WHERE state = 'PYTORCH_EPSILON_STATE_V3_LSTM'")
            row_eps = cursor.fetchone()
            if row_eps:
                eps_data = json.loads(row_eps[0])
                self.steps_done = eps_data.get("steps_done", 0)
                
            conn.close()
        except Exception as e:
            print(f"[!] PyTorch: Error loading weights: {e}")
