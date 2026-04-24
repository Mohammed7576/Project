import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np

class ActorCritic(nn.Module):
    """
    Point 7: Deep Actor-Critic (A2C) implementation.
    Actor: Selects the best mutation strategy based on WAF state.
    Critic: Estimates the success probability (Value) of the state.
    """
    def __init__(self, state_dim, action_dim):
        super(ActorCritic, self).__init__()
        # Shared layer for feature extraction
        self.affine = nn.Linear(state_dim, 64)
        
        # Actor head: Outputs probabilities for each mutation strategy
        self.action_head = nn.Linear(64, action_dim)
        
        # Critic head: Outputs the state value (Expected Reward)
        self.value_head = nn.Linear(64, 1)

    def forward(self, x):
        x = F.relu(self.affine(x))
        
        action_prob = F.softmax(self.action_head(x), dim=-1)
        state_values = self.value_head(x)
        
        return action_prob, state_values

class RLAgent:
    def __init__(self, state_dim, action_names):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.action_names = action_names
        self.model = ActorCritic(state_dim, len(action_names)).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.01)
        
        self.saved_actions = []
        self.rewards = []

    def select_action(self, state_vector):
        """Actor: Choosing the mutation strategy."""
        state = torch.from_numpy(np.array(state_vector)).float().unsqueeze(0).to(self.device)
        probs, state_value = self.model(state)
        
        # Create a categorical distribution over the list of probabilities of actions
        m = torch.distributions.Categorical(probs)
        action_idx = m.sample()
        
        # Save log probability and state value for training (Critic step)
        self.saved_actions.append((m.log_prob(action_idx), state_value))
        
        return self.action_names[action_idx.item()]

    def update(self, reward):
        """Critic: Optimization via Policy Gradient (Advantage)."""
        if not self.saved_actions: return
        
        # Use simple single-step update for demo efficiency
        log_prob, state_value = self.saved_actions[-1]
        
        # Advantage calculation: R - V(s)
        advantage = reward - state_value.item()
        
        # Policy Loss: -log_prob * Advantage
        policy_loss = -log_prob * advantage
        
        # Value Loss: Mean Squared Error of predicted value and actual reward
        value_loss = F.mse_loss(state_value, torch.tensor([[reward]]).to(self.device))
        
        loss = policy_loss + value_loss
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        self.saved_actions = [] # Reset after update
