import json
import logging
import os
from pathlib import Path
from typing import Any, Tuple

logger = logging.getLogger(__name__)

_default_dir = Path(__file__).resolve().parent.parent.parent / "models"
MODEL_PATH = Path(os.environ.get("RF_MODEL_PATH", _default_dir / "rf_cognitive.joblib"))
META_PATH = Path(os.environ.get("RF_META_PATH", _default_dir / "rf_cognitive.meta.json"))

_clf = None
_meta: dict[str, Any] | None = None
_load_attempted = False


def _load() -> Tuple[Any, dict[str, Any] | None]:
    global _clf, _meta, _load_attempted
    if _load_attempted:
        return _clf, _meta
    _load_attempted = True

    if not MODEL_PATH.is_file() or not META_PATH.is_file():
        logger.info("No RF artifact at %s / %s — model not ready.", MODEL_PATH, META_PATH)
        return None, None

    try:
        import joblib
    except ImportError:
        logger.warning("joblib not installed; cannot load RF model")
        return None, None

    try:
        clf = joblib.load(MODEL_PATH)
        meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("Failed to load RF model: %s", exc)
        _clf, _meta = None, None
        return _clf, _meta

    _clf, _meta = clf, meta
    logger.info("Loaded RF model from %s", MODEL_PATH)
    return _clf, _meta


def is_model_ready() -> bool:
    clf, meta = _load()
    return clf is not None and bool(meta)


def get_model() -> Any:
    clf, _ = _load()
    return clf


def get_metadata() -> dict[str, Any] | None:
    _, meta = _load()
    return meta
