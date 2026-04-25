def calculate_score(queue, total_waiting_time, predicted_queue, weights=None):
    """
    Calculate scoring for a lane.
    score = w1 * queue + w2 * avg_waiting_time + w3 * predicted_queue
    """
    if weights is None:
        weights = [1.0, 1.0, 1.0] # Default: queue, wait, predict
    
    w1, w2, w3 = weights
    
    # FIX: Priority Condition 1 - Empty lanes get ZERO score
    if queue == 0:
        return 0.0
        
    # FIX: Priority Condition 2 - Normalize wait time to average wait.
    # Total wait time explodes with 1 vehicle waiting 100s, but 10 cars waiting 10s is worse congestion.
    avg_waiting_time = total_waiting_time / queue if queue > 0 else 0
    
    # Priority condition: Large queues get exponential priority
    queue_penalty = queue * 1.5 if queue > 10 else queue
    
    score = (w1 * queue_penalty) + (w2 * avg_waiting_time) + (w3 * predicted_queue)
    return score
