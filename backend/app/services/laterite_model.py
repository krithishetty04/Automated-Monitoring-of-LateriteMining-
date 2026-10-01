"""Utility wrapper for the laterite grade classification model."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = Path(settings.LATERITE_MODEL_PATH) if settings.LATERITE_MODEL_PATH else PROJECT_ROOT / "images" / "best_resnet50_adam.keras"


def _safe_import_tensorflow():
    try:
        import tensorflow as tf
        return tf
    except ModuleNotFoundError:
        return None


def get_model_status() -> Dict[str, Any]:
    """Return the current status of the laterite grade model.

    This is intentionally lenient: the monitoring pipeline should continue even
    if the model is absent, while still reporting why it is unavailable.
    """
    tf = _safe_import_tensorflow()
    model_exists = MODEL_PATH.exists()

    if tf is None:
        return {
            "available": False,
            "model_path": str(MODEL_PATH),
            "reason": "tensorflow is not installed in the backend environment",
        }

    if not model_exists:
        return {
            "available": False,
            "model_path": str(MODEL_PATH),
            "reason": "model file was not found",
        }

    return {
        "available": True,
        "model_path": str(MODEL_PATH),
        "reason": "ready",
    }


def _find_sample_image() -> Optional[Path]:
    sample_root = PROJECT_ROOT / "images"
    if not sample_root.exists():
        return None

    supported = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
    candidates = sorted(sample_root.iterdir(), key=lambda p: p.name.lower())
    for candidate in candidates:
        if candidate.is_file() and candidate.suffix.lower() in supported:
            return candidate
    return None


def get_laterite_prediction_summary() -> Dict[str, Any]:
    """Return a simple UI-friendly laterite prediction payload for the frontend."""
    status = get_model_status()
    summary = {
        "available": status["available"],
        "model_path": status["model_path"],
        "reason": status["reason"],
        "grade": None,
        "confidence": None,
        "sample_image": None,
    }

    if not status["available"]:
        return summary

    sample_image = _find_sample_image()
    if sample_image is None:
        summary["reason"] = "model-ready-no-sample-image-found"
        return summary

    summary["sample_image"] = str(sample_image)
    prediction = maybe_predict_grade(str(sample_image))
    if prediction is None:
        summary["reason"] = "model-ready-but-inference-failed-on-sample-image"
        return summary

    summary["grade"] = prediction.get("grade")
    summary["confidence"] = prediction.get("confidence")
    summary["reason"] = "ready"
    return summary


def _load_model():
    tf = _safe_import_tensorflow()
    if tf is None:
        raise RuntimeError("tensorflow is not installed")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Laterite model not found at {MODEL_PATH}")

    return tf.keras.models.load_model(str(MODEL_PATH))


def maybe_predict_grade(image_path: Optional[str]) -> Optional[Dict[str, Any]]:
    """Predict a grade when an image path is supplied and the model is available."""
    if not image_path:
        return None

    status = get_model_status()
    if not status["available"]:
        return None

    try:
        import numpy as np
        import tensorflow as tf

        image_file = Path(image_path)
        if not image_file.exists():
            return None

        img = tf.keras.utils.load_img(str(image_file), target_size=(224, 224))
        image_array = tf.keras.utils.img_to_array(img)
        image_array = np.expand_dims(image_array, axis=0)
        image_array = tf.keras.applications.resnet50.preprocess_input(image_array)

        model = _load_model()
        predictions = model.predict(image_array, verbose=0)
        index = int(np.argmax(predictions[0]))
        confidence = float(predictions[0][index] * 100.0)

        labels = ["Grade A", "Grade B", "Grade C"]
        return {
            "grade": labels[index] if index < len(labels) else f"Grade {index + 1}",
            "confidence": round(confidence, 2),
            "raw_scores": [float(v) for v in predictions[0]],
        }
    except Exception:
        return None


def predict_laterite_from_image_path(image_path: Optional[str]) -> Dict[str, Any]:
    """Return a frontend-friendly prediction payload for an explicit image path."""
    status = get_model_status()
    payload = {
        "available": status["available"],
        "model_path": status["model_path"],
        "reason": status["reason"],
        "grade": None,
        "confidence": None,
        "sample_image": image_path,
    }

    if not status["available"]:
        return payload

    result = maybe_predict_grade(image_path)
    if result is None:
        payload["reason"] = "model-ready-but-inference-failed-on-image"
        return payload

    payload["grade"] = result.get("grade")
    payload["confidence"] = result.get("confidence")
    payload["reason"] = "ready"
    return payload
