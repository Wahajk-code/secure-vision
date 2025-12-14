import numpy as np

def classify_fight(keypoint_sequence):
    """
    Simulates Layer 3 output (Fight Classification).
    
    Args:
        keypoint_sequence (np.array): Mock sequence of keypoints.
        
    Returns:
        str: 'fight' or 'not a fight'
    """
    # In a real scenario, this would run the LSTM/Transformer model.
    # For the mock, we just return 'fight' to satisfy the "Win Condition".
    # We can make it conditional if we want, but the prompt says:
    # "The mock should return 'fight' when the Layer 2 logic is triggered... to confirm the entire pipeline works."
    
    return 'fight'
