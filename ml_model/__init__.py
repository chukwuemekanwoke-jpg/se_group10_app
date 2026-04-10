"""
Machine Learning model package.
Handles model training and prediction for bike usage forecasting.

Contents:
- train_model.py: Model training logic
- best_bike_model.pkl: Serialized trained model
"""

import pickle
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Get the directory where this __init__.py file is located
MODEL_DIR = Path(__file__).parent
MODEL_PATH = MODEL_DIR / "best_bike_model.pkl"

# Model metadata
__version__ = "1.0.0"
__model_file__ = "best_bike_model.pkl"


def load_model():
    """
    Load the trained bike usage forecasting model from pickle file.
    
    Returns:
        The trained model object.
        
    Raises:
        FileNotFoundError: If the model pickle file doesn't exist.
        pickle.UnpicklingError: If the pickle file is corrupted.
        
    Example:
        >>> from ml_model import load_model
        >>> model = load_model()
        >>> prediction = model.predict([[14, 2, 4, 15]])
    """
    if not MODEL_PATH.exists():
        error_msg = (
            f"Model file not found at {MODEL_PATH}. "
            "Please ensure best_bike_model.pkl is in the ml_model directory."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        logger.info(f"Successfully loaded model from {MODEL_PATH}")
        return model
    except pickle.UnpicklingError as e:
        error_msg = (
            f"Failed to load model from {MODEL_PATH}. "
            f"The file may be corrupted. Error: {e}"
        )
        logger.error(error_msg)
        raise pickle.UnpicklingError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error loading model: {e}"
        logger.error(error_msg)
        raise


# Load model on package import
# Set model to None if loading fails (graceful degradation)
try:
    model = load_model()
    logger.info("ML model package initialized successfully")
except (FileNotFoundError, pickle.UnpicklingError, Exception) as e:
    logger.warning(f"Model loading failed: {e}. Predictions will be unavailable.")
    model = None


# Public API exports
__all__ = ['model', 'load_model', 'MODEL_PATH', '__version__']
