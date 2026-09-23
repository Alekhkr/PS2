"""Domain enumerations for Signal Lab."""

from enum import Enum


class SourceFormat(str, Enum):
    WAV = "wav"
    IQ = "iq"
    RAW = "raw"
    SIGMF = "sigmf"


class SampleFormat(str, Enum):
    PCM16 = "pcm16"
    PCM24 = "pcm24"
    PCM32 = "pcm32"
    CF32 = "cf32"
    CF64 = "cf64"
    CI8 = "ci8"
    CI16 = "ci16"
    CI32 = "ci32"
    UNKNOWN = "unknown"


class ByteOrder(str, Enum):
    LITTLE_ENDIAN = "little"
    BIG_ENDIAN = "big"


class ModulationFamily(str, Enum):
    FSK = "FSK"
    BPSK = "BPSK"
    QPSK = "QPSK"
    PSK8 = "8PSK"
    QAM16 = "QAM16"
    QAM64 = "QAM64"
    UNKNOWN = "UNKNOWN"


class ValidationStatus(str, Enum):
    UNVERIFIED = "unverified"
    PARTIAL = "partial"
    VALIDATED = "validated"
    REJECTED = "rejected"


class EvidenceSource(str, Enum):
    FILE_HEADER = "file_header"
    USER = "user"
    ESTIMATOR = "estimator"
    CLASSIFIER = "classifier"
    DECODER = "decoder"


class JobState(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    STALE = "STALE"


class InterleaverType(str, Enum):
    BLOCK = "block"
    CONVOLUTIONAL = "convolutional"
    DIAGONAL = "diagonal"
    PSEUDO_RANDOM = "pseudo_random"
    NONE = "none"


class FECType(str, Enum):
    VITERBI = "viterbi"
    REED_SOLOMON = "reed_solomon"
    CONCATENATED = "concatenated"
    LDPC = "ldpc"
    NONE = "none"
