import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque

class QNetwork(nn.Module):
    """Multi-Layer Perceptron representing the Q-Network."""
    def __init__(self, state_size, action_size):
        super(QNetwork, self).__init__()
        self.fc1 = nn.Linear(state_size, 256)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(256, 256)
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(256, action_size)

    def forward(self, x):
        x = self.relu1(self.fc1(x))
        x = self.relu2(self.fc2(x))
        return self.fc3(x)

class DQNAgent:
    """Deep Q-Network Agent for Traffic Light Control."""
    def __init__(self, state_size=16, action_size=4, lr=2e-4, gamma=0.99, 
                 epsilon_start=1.0, epsilon_end=0.01, epsilon_decay=0.995, 
                 buffer_size=50000, batch_size=128):
        self.state_size = state_size
        self.action_size = action_size
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Q-Network and Target Network setup
        self.q_network = QNetwork(state_size, action_size).to(self.device)
        self.target_network = QNetwork(state_size, action_size).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()
        
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=lr)
        self.criterion = nn.MSELoss()
        
        # Experience replay buffer
        self.memory = deque(maxlen=buffer_size)

    def select_action(self, state, evaluate=False):
        """Select an action using epsilon-greedy policy."""
        # Explore
        if not evaluate and random.random() < self.epsilon:
            return random.choice(np.arange(self.action_size))
        
        # Exploit
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        self.q_network.eval()
        with torch.no_grad():
            action_values = self.q_network(state_tensor)
        self.q_network.train()
        
        return int(torch.argmax(action_values).item())

    def store_transition(self, state, action, reward, next_state, done):
        """Store experience in the replay buffer."""
        self.memory.append((state, action, reward, next_state, done))

    def learn(self):
        """Sample a batch from memory and update the Q-network."""
        if len(self.memory) < self.batch_size:
            return
        
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(np.array(states)).to(self.device)
        actions = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones = torch.FloatTensor(dones).unsqueeze(1).to(self.device)

        # Get current Q values
        current_q_values = self.q_network(states).gather(1, actions)
        
        # Get next Q values from target network
        with torch.no_grad():
            max_next_q_values = self.target_network(next_states).max(1)[0].unsqueeze(1)
            target_q_values = rewards + (1 - dones) * self.gamma * max_next_q_values
            
        loss = self.criterion(current_q_values, target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
    def update_target_network(self):
        """Update target network weights with Q-network weights."""
        self.target_network.load_state_dict(self.q_network.state_dict())
        
    def decay_epsilon(self):
        """Decay epsilon for epsilon-greedy policy."""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

