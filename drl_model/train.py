import os
import torch
import numpy as np
import matplotlib.pyplot as plt
from drl_model.environment import TrafficEnv
from drl_model.agent import DQNAgent

def train():
    """Main training loop for the DQN Agent interacting with the TrafficEnv."""
    env = TrafficEnv()
    
    state_size = 16
    action_size = int(env.action_space.n)
    agent = DQNAgent(state_size=state_size, action_size=action_size, lr=2e-4)
    
    num_episodes = 2500
    max_steps = 100
    target_update_freq = 20
    
    rewards_history = []
    
    print("Starting Training...")
    
    for episode in range(1, num_episodes + 1):
        state, _ = env.reset()
        episode_reward = 0
        
        for step in range(max_steps):
            action = agent.select_action(state)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            
            agent.store_transition(state, action, reward, next_state, done)
            agent.learn()
            
            state = next_state
            episode_reward += reward
            
            if done:
                break
                
        agent.decay_epsilon()
        
        if episode % target_update_freq == 0:
            agent.update_target_network()
            
        rewards_history.append(episode_reward)
        if episode % 50 == 0:
            print(f"Episode: {episode}/{num_episodes}, Reward: {episode_reward:.2f}, Epsilon: {agent.epsilon:.3f}")
            
    print("Training Completed.")
    
    # Save the model directly into drl_model for main.py to find
    model_path = os.path.join("drl_model", "dqn_agent.pth")
    torch.save(agent.q_network.state_dict(), model_path)
    print(f"Model saved to {model_path}")
    
    # Plotting training rewards
    plt.plot(rewards_history)
    plt.title("Training Reward over Episodes")
    plt.xlabel("Episode")
    plt.ylabel("Total Reward")
    os.makedirs("results", exist_ok=True)
    plt.savefig(os.path.join("results", "training_curve.png"))
    print("Training curve saved to results/training_curve.png")

if __name__ == "__main__":
    train()
