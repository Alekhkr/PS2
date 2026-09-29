"""High-performance ONNX Runtime inference for Automatic Modulation Classification."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

try:
    import onnxruntime as ort
    HAS_ONNX = True
except ImportError:
    HAS_ONNX = False

from signal_lab.ml.model import MODULATION_CLASSES_R16

logger = logging.getLogger(__name__)


class ONNXModulationClassifier:
    """Ultra-low latency inference runtime via ONNX/TensorRT."""

    def __init__(self, model_path: str | Path) -> None:
        if not HAS_ONNX:
            raise ImportError("onnxruntime is required. Install via `pip install onnxruntime`.")
            
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {self.model_path}")
            
        # Prioritize TensorRT (if available on GPU) then fallback to CPU execution provider
        providers = ["TensorrtExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider"]
        
        # Suppress verbose ONNX warnings during init
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        self.session = ort.InferenceSession(
            str(self.model_path), 
            sess_options=sess_options,
            providers=providers
        )
        
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def predict_probabilities(self, iq_samples: np.ndarray) -> np.ndarray:
        """
        Runs inference on complex IQ samples.
        
        Args:
            iq_samples: Complex numpy array of shape (N,) or (batch, N)
            
        Returns:
            Probabilities of shape (batch, num_classes)
        """
        if iq_samples.ndim == 1:
            iq_samples = np.expand_dims(iq_samples, 0)
            
        # Ensure 512 length (pad or truncate)
        target_len = 512
        b, n = iq_samples.shape
        if n > target_len:
            iq_samples = iq_samples[:, :target_len]
        elif n < target_len:
            pad = np.zeros((b, target_len - n), dtype=iq_samples.dtype)
            iq_samples = np.concatenate([iq_samples, pad], axis=1)
            
        # Convert to (Batch, Channels=2, Length)
        # 0 = Real (I), 1 = Imag (Q)
        tensor_in = np.zeros((b, 2, target_len), dtype=np.float32)
        tensor_in[:, 0, :] = np.real(iq_samples)
        tensor_in[:, 1, :] = np.imag(iq_samples)
        
        # Execute ONNX session iteratively since graph was exported with static batch=1
        logits_list = []
        for i in range(b):
            single_in = np.expand_dims(tensor_in[i], axis=0)
            out = self.session.run([self.output_name], {self.input_name: single_in})[0]
            logits_list.append(out)
            
        logits = np.concatenate(logits_list, axis=0)
        
        # Softmax
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        return probs

    def predict_class(self, iq_samples: np.ndarray) -> tuple[str, float]:
        """Returns the most likely modulation class and its confidence."""
        probs = self.predict_probabilities(iq_samples)
        class_idx = np.argmax(probs[0])
        confidence = float(probs[0][class_idx])
        
        class_name = MODULATION_CLASSES_R16[class_idx]
        return class_name, confidence

