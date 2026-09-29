"""Export PyTorch models to highly optimized ONNX graphs for inference."""

import argparse
from pathlib import Path

import torch

from signal_lab.ml.model import ModulationResNet1D, SignalBERT


def export_model(model_type: str, out_path: str) -> None:
    print(f"Initializing {model_type}...")
    
    if model_type == "resnet":
        model = ModulationResNet1D(in_channels=2, num_classes=16)
    elif model_type == "signalbert":
        model = SignalBERT(in_channels=2, num_classes=16, seq_len=512)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    model.eval()

    # Dummy input representing (Batch, Channels, Sequence_Length)
    dummy_input = torch.randn(1, 2, 512)

    print(f"Exporting to ONNX: {out_path}")
    torch.onnx.export(
        model,
        dummy_input,
        out_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input_iq"],
        output_names=["logits"],
    )
    
    print("Done. Model successfully exported to ONNX.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export AMC model to ONNX.")
    parser.add_argument("--model", type=str, choices=["resnet", "signalbert"], default="signalbert")
    parser.add_argument("--out", type=str, default="signal_lab/ml/weights/signalbert_opt.onnx")
    args = parser.parse_args()
    
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    export_model(args.model, args.out)
