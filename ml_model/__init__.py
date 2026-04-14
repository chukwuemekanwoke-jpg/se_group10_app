"""
ml_model/__init__.py - ML Model Loader with Lazy Initialization
Dublin Bikes Web App - COMP30830 Project - Troithean

Implements lazy loading to avoid loading the model on startup.
Model is only loaded on first prediction request.
"""

import logging
import joblib
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_model = None
_model_path = None


def _get_model_path():
    global _model_path
    if _model_path is None:
        current_dir = Path(__file__).parent
        _model_path = current_dir / 'best_bike_model.pkl'
        if not _model_path.exists():
            raise FileNotFoundError(
                f"ML model not found at {_model_path}. "
                "Make sure best_bike_model.pkl is in the ml_model/ directory."
            )
    return _model_path


def get_model():
    global _model

    if _model is not None:
        return _model

    try:
        model_path = _get_model_path()
        logger.info(f"Loading ML model from {model_path}...")

        # joblib.load() is the correct way to load sklearn models —
        # plain pickle.load() cannot handle joblib's NumpyArrayWrapper format
        _model = joblib.load(str(model_path))

        logger.info(
            f"✓ ML model loaded successfully "
            f"(size: {model_path.stat().st_size / (1024*1024):.1f}MB)"
        )
        return _model

    except FileNotFoundError as e:
        logger.error(f"Model file not found: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error loading ML model: {e}", exc_info=True)
        return None


def clear_model_cache():
    global _model
    _model = None
    logger.info("ML model cache cleared")


def get_model_info():
    model_path = _get_model_path()
    file_size_mb = model_path.stat().st_size / (1024*1024)
    return {
        "path": str(model_path),
        "file_size_mb": f"{file_size_mb:.1f}",
        "loaded": _model is not None,
        "model_type": type(_model).__name__ if _model else "not loaded",
    }


try:
    model = None
except Exception:
    model = None
