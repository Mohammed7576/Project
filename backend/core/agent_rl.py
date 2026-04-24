import numpy as np

class RLAgent:
    """
    Point 7: Deep Actor-Critic (A2C) implementation using NumPy.
    Actor: Base policy for mutation selection.
    Critic: Value estimation.
    """
    def __init__(self, state_dim, action_names):
        self.state_dim = state_dim
        self.action_names = action_names
        self.action_dim = len(action_names)
        self.lr = 0.01
        
        # Simple Neural Network Weights (One hidden layer)
        self.W1 = np.random.randn(state_dim, 32) * 0.1
        self.W_actor = np.random.randn(32, self.action_dim) * 0.1
        self.W_critic = np.random.randn(32, 1) * 0.1
        
        self.last_state = None
        self.last_action_idx = None

    def _softmax(self, x):
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()

    def select_action(self, state_vector):
        """Actor: Forward pass to choose mutation."""
        state = np.array(state_vector).reshape(1, -1)
        
        # Forward pass
        h = np.tanh(np.dot(state, self.W1))
        probs = self._softmax(np.dot(h, self.W_actor))[0]
        
        # Sample action from distribution
        action_idx = np.random.choice(self.action_dim, p=probs)
        
        self.last_state = state
        self.last_action_idx = action_idx
        self.last_h = h
        self.last_probs = probs
        
        return self.action_names[action_idx]

    def update(self, reward):
        """Critic: Simple Policy Gradient update (Backpropagation)."""
        if self.last_state is None: return
        
        # Multi-variable advantage
        # Target value is the reward
        # Current value prediction
        value_pred = np.dot(self.last_h, self.W_critic)[0, 0]
        advantage = reward - value_pred
        
        # 1. Update Critic (MSE Loss)
        # Grad of (reward - V)^2 -> 2 * (reward - V) * -h
        dv = -2 * advantage
        dW_critic = np.dot(self.last_h.T, np.array([[dv]]))
        self.W_critic -= self.lr * dW_critic
        
        # 2. Update Actor (Policy Gradient)
        # Grad of -log(prob) * advantage
        d_actor = self.last_probs.copy()
        d_actor[self.last_action_idx] -= 1.0 # Softmax gradient
        d_actor *= advantage
        
        dW_actor = np.dot(self.last_h.T, d_actor.reshape(1, -1))
        self.W_actor -= self.lr * dW_actor
        
        # Simplification: Only updating heads, hidden layer fixed for stability in small runs
        
        self.last_state = None # Reset
