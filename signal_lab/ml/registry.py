"""Local Model Registry for versioned offline inference models."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from signal_lab.storage.database import get_default_storage_dir


@dataclass
class ModelRecord:
    model_id: str
    version: str
    training_dataset: str
    classes: list[str]
    input_type: str = "iq_window"
    metrics: dict[str, float] = field(default_factory=dict)
    weights_path: str | None = None
    created_at: str = ""


class LocalModelRegistry:
    """Manages offline ML model versions and evaluation records."""

    def __init__(self, registry_dir: str | Path | None = None) -> None:
        self.registry_dir = Path(registry_dir or get_default_storage_dir() / "models")
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self._models_file = self.registry_dir / "registry.json"
        self._models: dict[str, ModelRecord] = {}
        self._load()

    def _load(self) -> None:
        if self._models_file.exists():
            try:
                with open(self._models_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.values():
                        rec = ModelRecord(**item)
                        self._models[f"{rec.model_id}:{rec.version}"] = rec
            except (json.JSONDecodeError, OSError):
                self._models = {}

    def _save(self) -> None:
        with open(self._models_file, "w", encoding="utf-8") as f:
            data = {k: asdict(v) for k, v in self._models.items()}
            json.dump(data, f, indent=2)

    def register_model(self, record: ModelRecord) -> None:
        key = f"{record.model_id}:{record.version}"
        self._models[key] = record
        self._save()

    def get_model(self, model_id: str, version: str | None = None) -> ModelRecord | None:
        if version:
            return self._models.get(f"{model_id}:{version}")
        # Return latest registered version
        matching = [m for m in self._models.values() if m.model_id == model_id]
        if not matching:
            return None
        return matching[-1]

    def list_models(self) -> list[ModelRecord]:
        return list(self._models.values())
