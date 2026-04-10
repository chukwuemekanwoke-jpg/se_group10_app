"""
Machine Learning model package.
Handles model training and prediction for bike usage forecasting.
Contents:
- train_model.py: Model training logic
- best_bike_model.pkl: Serialized trained model
"""

import pickle
import os
from pathlib import Path

# Get the directory where this __init__.py file is located
MODEL_DIR = Path(__file__).parent

# Path to the serialized model
MODEL_PATH = MODEL_DIR / "best_bike_model.pkl"


def load_model():
    """
    Load the trained bike usage forecasting model from pickle file.
    
    Returns:
        The trained model object, or None if model file not found.
        
    Raises:
        FileNotFoundError: If the model pickle file doesn't exist.
        pickle.UnpicklingError: If the pickle file is corrupted.
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found at {MODEL_PATH}. "
            "Please ensure best_bike_model.pkl is in the ml_model directory."
        )
    
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        return model
    except pickle.UnpicklingError as e:
        raise pickle.UnpicklingError(
            f"Failed to load model from {MODEL_PATH}. The file may be corrupted. Error: {e}"
        )


# Load model on package import
try:
    model = load_model()
except FileNotFoundError as e:
    print(f"Warning: {e}")
    model = None


# Export public API
__all__ = ['model', 'load_model', 'MODEL_PATH']
