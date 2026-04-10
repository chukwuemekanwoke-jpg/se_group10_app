"""
ml_model/__init__.py - ML Model Loader with Lazy Initialization
Dublin Bikes Web App - COMP30830 Project - Troithean

Implements lazy loading to avoid loading 42MB model on startup.
Model is only loaded on first prediction request.

Usage:
    from ml_model import get_model
    model = get_model()
    predictions = model.predict(features)
"""

import logging
import pickle
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Module-level variable to cache loaded model
_model = None
_model_path = None


def _get_model_path():
    """
    Get the path to the pickled ML model.
    
    Returns:
        Path: Path object to best_bike_model.pkl
        
    Raises:
        FileNotFoundError: If model file doesn't exist
    """
    global _model_path
    
    if _model_path is None:
        # Get the directory where this file is located
        current_dir = Path(__file__).parent
        _model_path = current_dir / 'best_bike_model.pkl'
        
        if not _model_path.exists():
            raise FileNotFoundError(
                f"ML model not found at {_model_path}. "
                "Make sure best_bike_model.pkl is in the ml_model/ directory."
            )
    
    return _model_path


def get_model():
    """
    Get the loaded ML model, loading it lazily on first call.
    
    The model is loaded from disk only on first call and then cached
    in memory for subsequent calls. This avoids loading 42MB at startup
    and reduces memory pressure on t3.micro instances.
    
    Returns:
        sklearn model: Loaded scikit-learn model for predictions
        None: If model fails to load
        
    Example:
        >>> model = get_model()
        >>> if model:
        ...     prediction = model.predict([[1, 2, 3, 4, 5, 6, 7, 8]])
        ... else:
        ...     print("Model unavailable")
    """
    global _model
    
    # Return cached model if already loaded
    if _model is not None:
        return _model
    
    try:
        model_path = _get_model_path()
        
        logger.info(f"Loading ML model from {model_path}...")
        
        with open(str(model_path), 'rb') as f:
            _model = pickle.load(f)
        
        logger.info(
            f"✓ ML model loaded successfully "
            f"(size: {model_path.stat().st_size / (1024*1024):.1f}MB)"
        )
        
        return _model
        
    except FileNotFoundError as e:
        logger.error(f"Model file not found: {e}")
        return None
        
    except pickle.UnpicklingError as e:
        logger.error(f"Failed to unpickle model: {e}")
        return None
        
    except Exception as e:
        logger.error(
            f"Unexpected error loading ML model: {e}",
            exc_info=True
        )
        return None


def clear_model_cache():
    """
    Clear the cached model from memory.
    
    Useful for testing or reloading the model.
    
    Example:
        >>> clear_model_cache()
        >>> model = get_model()  # Reloads from disk
    """
    global _model
    _model = None
    logger.info("ML model cache cleared")


def get_model_info():
    """
    Get information about the loaded model.
    
    Returns:
        dict: Model metadata (name, type, loaded status)
    """
    model_path = _get_model_path()
    file_size_mb = model_path.stat().st_size / (1024*1024)
    
    return {
        "path": str(model_path),
        "file_size_mb": f"{file_size_mb:.1f}",
        "loaded": _model is not None,
        "model_type": type(_model).__name__ if _model else "not loaded",
    }


# For backwards compatibility if code imports 'model' directly
try:
    model = None  # Will be set on first get_model() call
except Exception:
    model = None
