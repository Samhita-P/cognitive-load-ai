import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_default_dir = Path(__file__).resolve().parent.parent.parent / "models"

MODEL_PATH = Path(
    os.environ.get("RF_MODEL_PATH", _default_dir / "rf_cognitive.joblib")
)

META_PATH = Path(
    os.environ.get("RF_META_PATH", _default_dir / "rf_cognitive.meta.json")
)


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
            logger.info(
                "No RF artifact found at %s / %s. Falling back to heuristic engine.",
                MODEL_PATH,
                META_PATH,
            )
            return

        try:
            import joblib

            cls._clf = joblib.load(MODEL_PATH)
            cls._meta = json.loads(META_PATH.read_text(encoding="utf-8"))

            # -------------------------------
            # Metadata validation
            # -------------------------------
            if not isinstance(cls._meta, dict):
                raise RuntimeError("Metadata is not a JSON object")

            if "features" not in cls._meta:
                raise RuntimeError("Model metadata missing 'features'")

            if "classes" not in cls._meta:
                raise RuntimeError("Model metadata missing 'classes'")

            # Backward compatibility for old artifacts
            schema_version = cls._meta.get("schema_version", "legacy")

            if schema_version not in {"v1", "legacy"}:
                raise RuntimeError(
                    f"Unsupported schema version: {schema_version}"
                )

            # -------------------------------
            # Model validation
            # -------------------------------
            if not hasattr(cls._clf, "predict_proba"):
                raise RuntimeError(
                    "Loaded model does not support predict_proba"
                )

            expected_feature_count = len(cls._meta["features"])

            if hasattr(cls._clf, "n_features_in_"):
                if cls._clf.n_features_in_ != expected_feature_count:
                    raise RuntimeError(
                        f"Model feature count mismatch "
                        f"({cls._clf.n_features_in_} vs {expected_feature_count})"
                    )

            # Strict ordering validation only if available
            if hasattr(cls._clf, "feature_names_in_"):
                model_features = list(cls._clf.feature_names_in_)
                meta_features = cls._meta["features"]

                if model_features != meta_features:
                    raise RuntimeError(
                        f"Model feature ordering mismatch. "
                        f"Expected {meta_features}, got {model_features}"
                    )

            logger.info(
                "RF model loaded successfully from %s (schema=%s)",
                MODEL_PATH,
                schema_version,
            )

        except ImportError:
            logger.warning(
                "joblib not installed. Falling back to heuristic engine."
            )
            cls._clf = None
            cls._meta = None

        except Exception as exc:
            logger.error("Failed to load model: %s", exc)
            raise RuntimeError(f"Model startup validation failed: {exc}")

    @classmethod
    def is_model_ready(cls) -> bool:
        return cls._clf is not None and cls._meta is not None

    @classmethod
    def get_model(cls) -> Any:
        return cls._clf

    @classmethod
    def get_metadata(cls) -> dict[str, Any] | None:
        return cls._meta


# Backward compatibility exports
is_model_ready = ModelRegistry.is_model_ready
get_model = ModelRegistry.get_model
get_metadata = ModelRegistry.get_metadata