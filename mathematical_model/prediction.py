def predict_queue(current_queue, growth_rate, lookahead_steps=10):
    """
    Simple prediction model.
    predicted_queue = current_queue + (growth_rate * lookahead_steps)
    """
    return max(0, current_queue + (growth_rate * lookahead_steps))
