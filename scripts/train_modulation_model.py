"""Training script for Automatic Modulation Classification using RadioMod-R16.

Trains the compact ModulationResNet1D on 16 modulation families with SNR stratification.
Saves model weights to signal_lab/ml/weights/modulation_r16_resnet.pt.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import h5py
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from signal_lab.ml.model import MODULATION_CLASSES_R16, ModulationResNet1D


def load_dataset(h5_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Loads X, Y, Z from RadioMod-R16 HDF5 file."""
    print(f"Loading dataset from {h5_path}...")
    with h5py.File(h5_path, "r") as f:
        x = f["X"][:]  # (16800, 512, 2)
        y = f["Y"][:]  # (16800, 16)
        z = f["Z"][:]  # (16800,)

    # Convert one-hot Y to class indices
    labels = np.argmax(y, axis=1)

    # Transpose X to (N, 2, 512) for Conv1d
    x = np.transpose(x, (0, 2, 1)).astype(np.float32)

    print(f"Loaded: X={x.shape}, labels={labels.shape}, SNR range=[{z.min():.1f}, {z.max():.1f}] dB")
    return x, labels, z


def train_model(
    data_path: str = "data/RadioMod-R16 dataset.h5",
    output_weights: str = "signal_lab/ml/weights/modulation_r16_resnet.pt",
    epochs: int = 15,
    batch_size: int = 64,
    lr: float = 1e-3,
    device_str: str = "cpu",
) -> None:
    h5_path = Path(data_path)
    if not h5_path.exists():
        raise FileNotFoundError(f"Dataset not found at {h5_path}")

    device = torch.device(device_str)
    x, y, z = load_dataset(h5_path)

    # Train / Val / Test split (80% / 10% / 10%)
    n_samples = len(x)
    indices = np.random.RandomState(42).permutation(n_samples)
    n_train = int(0.80 * n_samples)
    n_val = int(0.10 * n_samples)

    train_idx = indices[:n_train]
    val_idx = indices[n_train : n_train + n_val]
    test_idx = indices[n_train + n_val :]

    x_train, y_train = torch.tensor(x[train_idx]), torch.tensor(y[train_idx], dtype=torch.long)
    x_val, y_val = torch.tensor(x[val_idx]), torch.tensor(y[val_idx], dtype=torch.long)
    x_test, y_test, z_test = (
        torch.tensor(x[test_idx]),
        torch.tensor(y[test_idx], dtype=torch.long),
        z[test_idx],
    )

    train_loader = DataLoader(
        TensorDataset(x_train, y_train), batch_size=batch_size, shuffle=True
    )
    val_loader = DataLoader(TensorDataset(x_val, y_val), batch_size=batch_size, shuffle=False)

    model = ModulationResNet1D(num_classes=len(MODULATION_CLASSES_R16)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    print(f"Starting training on {device} for {epochs} epochs...")
    best_val_acc = 0.0
    best_state = None

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        model.train()
        total_loss, correct, total = 0.0, 0, 0

        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            logits = model(batch_x)
            loss = criterion(logits, batch_y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(batch_y)
            preds = torch.argmax(logits, dim=1)
            correct += (preds == batch_y).sum().item()
            total += len(batch_y)

        scheduler.step()
        train_loss = total_loss / total
        train_acc = correct / total

        # Validation
        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                logits = model(batch_x)
                preds = torch.argmax(logits, dim=1)
                val_correct += (preds == batch_y).sum().item()
                val_total += len(batch_y)

        val_acc = val_correct / val_total
        elapsed = time.time() - t0
        print(
            f"Epoch {epoch:02d}/{epochs:02d} [{elapsed:.1f}s] - "
            f"Loss: {train_loss:.4f} | Train Acc: {train_acc * 100:.1f}% | Val Acc: {val_acc * 100:.1f}%"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_state = model.state_dict().copy()

    # Save best model
    out_path = Path(output_weights)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if best_state is not None:
        torch.save(best_state, out_path)
        print(f"\nSaved best model (Val Acc: {best_val_acc * 100:.2f}%) to {out_path}")

    # Evaluate Test Set by SNR
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        test_logits = model(x_test.to(device))
        test_preds = torch.argmax(test_logits, dim=1).cpu().numpy()
        test_targets = y_test.numpy()

    overall_acc = np.mean(test_preds == test_targets)
    print("\n==========================================")
    print(f"Overall Test Accuracy: {overall_acc * 100:.2f}%")
    print("==========================================")

    # Per-SNR breakdown
    unique_snrs = np.unique(z_test)
    print("Test Accuracy by SNR:")
    for snr_val in sorted(unique_snrs):
        mask = z_test == snr_val
        if np.any(mask):
            snr_acc = np.mean(test_preds[mask] == test_targets[mask])
            print(f"  SNR {snr_val:5.1f} dB: {snr_acc * 100:5.1f}% ({np.sum(mask)} samples)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train AMC model on RadioMod-R16")
    parser.add_argument("--epochs", type=int, default=12, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    args = parser.parse_args()

    train_model(epochs=args.epochs, batch_size=args.batch_size)
