import numpy as np

class RLAgent:
    """
    Point 7: Enhanced Actor-Critic with Experience Replay.
    Actor: Base policy for mutation selection.
    Critic: Value estimation learned from a history of experiences.
    """
    def __init__(self, state_dim, action_names):
        self.state_dim = state_dim
        self.action_names = action_names
        self.action_dim = len(action_names)
        self.lr = 0.01
        self.gamma = 0.95 # Discount factor for future rewards
        
        # Simple Neural Network Weights
        self.W1 = np.random.randn(state_dim, 64) * 0.1
        self.W_actor = np.random.randn(64, self.action_dim) * 0.1
        self.W_critic = np.random.randn(64, 1) * 0.1
        
        # Experience Replay Buffer
        self.memory = []
        self.max_memory = 500
        
        self.last_state = None
        self.last_action_idx = None

    def get_weights(self):
        """Serializes neural network weights for persistence."""
        return {
            "W1": self.W1.tolist(),
            "W_actor": self.W_actor.tolist(),
            "W_critic": self.W_critic.tolist(),
            "memory": [ [s.tolist(), a, r, (ns.tolist() if ns is not None else None)] for s, a, r, ns in self.memory ]
        }

    def load_weights(self, weights):
        """Loads neural network weights from serialized data."""
        if not weights: return
        try:
            self.W1 = np.array(weights["W1"])
            self.W_actor = np.array(weights["W_actor"])
            self.W_critic = np.array(weights["W_critic"])
            self.memory = []
            for s, a, r, ns in weights.get("memory", []):
                self.memory.append((np.array(s), a, r, (np.array(ns) if ns is not None else None)))
        except Exception as e:
            print(f"[!] RL Agent: Error loading weights: {e}")

    def _softmax(self, x):
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()

    def select_action(self, state_vector):
        """Actor: Forward pass to choose mutation with noise for exploration."""
        state = np.array(state_vector).reshape(1, -1)
        h = np.tanh(np.dot(state, self.W1))
        probs = self._softmax(np.dot(h, self.W_actor))[0]
        
        # Add a bit of epsilon-greedy for exploration
        if np.random.random() < 0.05:
            action_idx = np.random.choice(self.action_dim)
        else:
            action_idx = np.random.choice(self.action_dim, p=probs)
        
        self.last_state = state
        self.last_action_idx = action_idx
        self.last_h = h
        self.last_probs = probs
        
        return self.action_names[action_idx]

    def store_experience(self, state, action_idx, reward, next_state):
        """Adds observation to memory for batch learning."""
        self.memory.append((state, action_idx, reward, next_state))
        if len(self.memory) > self.max_memory:
            self.memory.pop(0)

    def update(self, reward):
        """Critic: Batch update from memory to stabilize training."""
        if self.last_state is None: return
        
        # Store current experience
        self.store_experience(self.last_state, self.last_action_idx, reward, None)
        
        # Learn from a small batch of history (Stochastic Gradient Descent)
        batch_size = min(len(self.memory), 16)
        batch_indices = np.random.choice(len(self.memory), batch_size, replace=False)
        
        for idx in batch_indices:
            s, a, r, _ = self.memory[idx]
            
            # Re-calculating forward for the sampled state
            h = np.tanh(np.dot(s, self.W1))
            probs = self._softmax(np.dot(h, self.W_actor))[0]
            val = np.dot(h, self.W_critic)[0, 0]
            
            # Advantange estimation
            advantage = r - val
            
            # 1. Update Critic (Value Head)
            dv = -2 * advantage
            self.W_critic -= self.lr * np.dot(h.T, np.array([[dv]]))
            
            # 2. Update Actor (Policy Head)
            d_actor = probs.copy()
            d_actor[a] -= 1.0
            d_actor *= advantage
            self.W_actor -= self.lr * np.dot(h.T, d_actor.reshape(1, -1))
            
            # 3. Hidden layer update (Backprop through Tanh)
            # Simplification: Only update W1 based on actor grad to steer feature extraction
            dh = np.dot(d_actor.reshape(1, -1), self.W_actor.T) * (1 - h**2)
            self.W1 -= self.lr * np.dot(s.T, dh)

        self.last_state = None
