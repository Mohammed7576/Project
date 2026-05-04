import numpy as np

class RLAgent:
    """
    Point 7: Enhanced Actor-Critic with Experience Replay.
    Actor: Base policy for mutation selection.
    Critic: Value estimation learned from a history of experiences.
    """
    def __init__(self, state_dim, action_names, learning_rate=0.1, exploration_rate=0.05):
        self.state_dim = state_dim
        self.action_names = action_names
        self.action_dim = len(action_names)
        self.lr = learning_rate
        self.epsilon = exploration_rate
        self.gamma = 0.95 # Discount factor for future rewards
        
        # Simple Neural Network Weights
        self.W1 = np.random.randn(state_dim, 64) * 0.1
        self.W_actor = np.random.randn(64, self.action_dim) * 0.1
        self.W_critic = np.random.randn(64, 1) * 0.1
        
        # Experience Replay Buffer
        self.memory = []
        self.max_memory = 100
        
        self.last_state = None
        self.last_action_idx = None

    def _softmax(self, x):
        # Subtract max for numerical stability
        x = x - np.max(x, axis=-1, keepdims=True)
        e_x = np.exp(x)
        return e_x / e_x.sum(axis=-1, keepdims=True)

    def select_action(self, state_vector):
        """Actor: Forward pass to choose mutation with noise for exploration."""
        state = np.array(state_vector).reshape(1, -1)
        h = np.tanh(np.dot(state, self.W1))
        probs = self._softmax(np.dot(h, self.W_actor))[0]
        
        # Ensure exact sum to 1.0 to prevent ValueError in np.random.choice
        probs = probs / np.sum(probs)
        
        # Add a bit of epsilon-greedy for exploration
        if np.random.random() < self.epsilon:
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
        batch_size = min(len(self.memory), 64)
        batch_indices = np.random.choice(len(self.memory), batch_size, replace=False)
        
        for idx in batch_indices:
            s, a, r, _ = self.memory[idx]
            
            # Re-calculating forward for the sampled state
            h = np.tanh(np.dot(s, self.W1))
            probs = self._softmax(np.dot(h, self.W_actor))[0]
            val = np.dot(h, self.W_critic)[0, 0]
            
            # Advantange estimation
            advantage = r - val
            
            # Keep original weights for correct backprop
            W_critic_old = self.W_critic.copy()
            W_actor_old = self.W_actor.copy()
            
            # 1. Update Critic (Value Head)
            dv = -2 * advantage
            d_critic = np.array([[dv]])
            self.W_critic -= self.lr * np.dot(h.T, d_critic)
            
            # 2. Update Actor (Policy Head)
            d_actor = probs.copy()
            d_actor[a] -= 1.0
            d_actor *= advantage
            self.W_actor -= self.lr * np.dot(h.T, d_actor.reshape(1, -1))
            
            # 3. Hidden layer update (Backprop through Tanh)
            # Combine Actor and Critic gradients accurately
            dh_actor = np.dot(d_actor.reshape(1, -1), W_actor_old.T)
            dh_critic = np.dot(d_critic, W_critic_old.T)
            dh = (dh_actor + dh_critic) * (1 - h**2)
            self.W1 -= self.lr * np.dot(s.T, dh)

        self.last_state = None
