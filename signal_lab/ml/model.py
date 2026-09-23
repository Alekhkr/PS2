"""Deep Learning architectures for Automatic Modulation Classification (AMC).

Implements a lightweight 1D Residual Convolutional Neural Network (ResNet-1D)
optimized for sub-2ms CPU inference on complex IQ vectors of shape (B, 2, 512).
"""

from __future__ import annotations

try:
    import torch
    import torch.nn.functional as F
    from torch import nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    nn = object  # type: ignore[assignment,misc]


# Standard 16 modulation classes from RadioMod-R16
MODULATION_CLASSES_R16 = [
    "BPSK",
    "QPSK",
    "8PSK",
    "OQPSK",
    "DQPSK",
    "Pi/4-QPSK",
    "16QAM",
    "32QAM",
    "64QAM",
    "16APSK",
    "2FSK",
    "4FSK",
    "MSK",
    "CPFSK",
    "GMSK",
    "GFSK",
]


if HAS_TORCH:

    class ResidualBlock1D(nn.Module):
        """1D Residual convolutional block with skip connection and batch normalization."""

        def __init__(self, channels: int, kernel_size: int = 5) -> None:
            super().__init__()
            padding = kernel_size // 2
            self.conv1 = nn.Conv1d(channels, channels, kernel_size=kernel_size, padding=padding)
            self.bn1 = nn.BatchNorm1d(channels)
            self.conv2 = nn.Conv1d(channels, channels, kernel_size=kernel_size, padding=padding)
            self.bn2 = nn.BatchNorm1d(channels)
            self.relu = nn.ReLU(inplace=True)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            residual = x
            out = self.relu(self.bn1(self.conv1(x)))
            out = self.bn2(self.conv2(out))
            out = self.relu(out + residual)
            return out

    class ModulationResNet1D(nn.Module):
        """Compact 1D ResNet for Automatic Modulation Classification.

        Input shape: (batch_size, 2, sequence_length), where channels: 0=I, 1=Q.
        Output: Logits over num_classes (default 16).
        """

        def __init__(
            self,
            in_channels: int = 2,
            num_classes: int = 16,
            base_filters: int = 32,
        ) -> None:
            super().__init__()
            self.in_channels = in_channels
            self.num_classes = num_classes

            # Stem
            self.stem = nn.Sequential(
                nn.Conv1d(in_channels, base_filters, kernel_size=7, stride=2, padding=3),
                nn.BatchNorm1d(base_filters),
                nn.ReLU(inplace=True),
            )

            # Stage 1: 32 channels
            self.layer1 = nn.Sequential(
                ResidualBlock1D(base_filters, kernel_size=5),
                nn.MaxPool1d(kernel_size=2),
            )

            # Stage 2: 64 channels
            self.trans1 = nn.Sequential(
                nn.Conv1d(base_filters, base_filters * 2, kernel_size=1),
                nn.BatchNorm1d(base_filters * 2),
                nn.ReLU(inplace=True),
            )
            self.layer2 = nn.Sequential(
                ResidualBlock1D(base_filters * 2, kernel_size=5),
                nn.MaxPool1d(kernel_size=2),
            )

            # Stage 3: 128 channels
            self.trans2 = nn.Sequential(
                nn.Conv1d(base_filters * 2, base_filters * 4, kernel_size=1),
                nn.BatchNorm1d(base_filters * 4),
                nn.ReLU(inplace=True),
            )
            self.layer3 = nn.Sequential(
                ResidualBlock1D(base_filters * 4, kernel_size=3),
                nn.AdaptiveAvgPool1d(1),
            )

            # Head
            self.fc = nn.Sequential(
                nn.Dropout(p=0.3),
                nn.Linear(base_filters * 4, 64),
                nn.ReLU(inplace=True),
                nn.Linear(64, num_classes),
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            out = self.stem(x)
            out = self.layer1(out)
            out = self.trans1(out)
            out = self.layer2(out)
            out = self.trans2(out)
            out = self.layer3(out)
            out = torch.flatten(out, 1)
            logits = self.fc(out)
            return logits

        def predict_probabilities(self, x: torch.Tensor) -> torch.Tensor:
            """Evaluates input and returns softmax probabilities."""
            self.eval()
            with torch.no_grad():
                logits = self.forward(x)
                return F.softmax(logits, dim=-1)

else:
    # Fallback placeholder when torch is not available
    class ModulationResNet1D:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:
            raise ImportError("PyTorch is required for ModulationResNet1D")
