import json
import logging
import os
from pathlib import Path
from typing import Any, Tuple

logger = logging.getLogger(__name__)

_default_dir = Path(__file__).resolve().parent.parent.parent / "models"
MODEL_PATH = Path(os.environ.get("RF_MODEL_PATH", _default_dir / "rf_cognitive.joblib"))
META_PATH = Path(os.environ.get("RF_META_PATH", _default_dir / "rf_cognitive.meta.json"))

class ModelRegistry:
    _clf = None
    _meta: dict[str, Any] | None = None
    _load_attempted = False

    @classmethod
    def load_once(cls):
        if cls._load_attempted:
            return
        cls._load_attempted = True

        if not MODEL_PATH.is_file() or not META_PATH.is_file():
            logger.info("No RF artifact at %s / %s — model not ready.", MODEL_PATH, META_PATH)
            return

        try:
            import joblib
            cls._clf = joblib.load(MODEL_PATH)
            cls._meta = json.loads(META_PATH.read_text(encoding="utf-8"))
            
            # Explicit Schema Validation
            if not isinstance(cls._meta, dict):
                raise RuntimeError("Metadata is not a JSON object")
            if "features" not in cls._meta or "classes" not in cls._meta:
                raise RuntimeError("Model metadata is missing 'features' or 'classes' schema definition")
            
            if "schema_version" not in cls._meta:
                raise RuntimeError("Model metadata is missing 'schema_version'")
            if cls._meta["schema_version"] != "v1":
                raise RuntimeError(f"Unsupported schema version: {cls._meta['schema_version']}")

            if not hasattr(cls._clf, "predict_proba"):
                raise RuntimeError("Loaded model does not have a 'predict_proba' method")
            
            # Validate model feature dimension matches metadata
            expected_feature_count = len(cls._meta["features"])
            if hasattr(cls._clf, "n_features_in_") and cls._clf.n_features_in_ != expected_feature_count:
                 raise RuntimeError(f"Model feature count ({cls._clf.n_features_in_}) does not match metadata ({expected_feature_count})")
                 
            # Validate feature ordering if exposed by the model (scikit-learn >= 1.0)
            if not hasattr(cls._clf, "feature_names_in_"):
                raise RuntimeError("Model artifact missing feature_names_in_. Ensure the model is trained with a modern scikit-learn version that persists feature names.")
                
            model_features = list(cls._clf.feature_names_in_)
            meta_features = cls._meta["features"]
            if model_features != meta_features:
                 raise RuntimeError(f"Model feature ordering mismatch. Expected {meta_features}, got {model_features}")
                 
            logger.info("Loaded and validated RF model from %s", MODEL_PATH)
        except ImportError:
            logger.warning("joblib not installed; cannot load RF model")
            # Don't raise RuntimeError here to allow fallback to heuristic if intended, but let's assume if it's there it should work
        except Exception as exc:
            logger.error("Failed to load or validate RF model: %s", exc)
            if isinstance(exc, RuntimeError):
                raise
            raise RuntimeError(f"Failed to load or validate RF model: {exc}")

    @classmethod
    def is_model_ready(cls) -> bool:
        return cls._clf is not None and bool(cls._meta)

    @classmethod
    def get_model(cls) -> Any:
        return cls._clf

    @classmethod
    def get_metadata(cls) -> dict[str, Any] | None:
        return cls._meta

# For backwards compatibility with other files if any are importing these
is_model_ready = ModelRegistry.is_model_ready
get_model = ModelRegistry.get_model
get_metadata = ModelRegistry.get_metadata
