#!/usr/bin/env bash
# Create the Python environments the tooling needs. They live outside the synced show folder.
#   audio      - librosa, matplotlib, Demucs (CPU-only PyTorch)
#   basicpitch - Spotify Basic Pitch (ONNX backend)
set -euo pipefail
CACHE="${XLIGHTS_TOOLING_CACHE:-$HOME/.cache/xlights-tooling}"
V="$CACHE/venvs"
mkdir -p "$V"

if command -v uv >/dev/null; then
    UV=uv
else
    [ -x "$V/bootstrap/bin/uv" ] || { python3 -m venv "$V/bootstrap" && "$V/bootstrap/bin/pip" install -q uv; }
    UV="$V/bootstrap/bin/uv"
fi

if [ ! -x "$V/audio/bin/python" ]; then
    echo "creating $V/audio ..."
    "$UV" venv -q -p 3.11 "$V/audio"
    # the default torch wheel drags in ~5 GB of CUDA libraries; take the CPU build
    "$UV" pip install -q -p "$V/audio/bin/python" \
        --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple \
        --index-strategy unsafe-best-match torch torchaudio demucs soundfile librosa matplotlib faster-whisper zstandard
fi

if [ ! -x "$V/basicpitch/bin/basic-pitch" ]; then
    echo "creating $V/basicpitch ..."
    "$UV" venv -q -p 3.11 "$V/basicpitch"
    "$UV" pip install -q -p "$V/basicpitch/bin/python" "basic-pitch[onnx]" "setuptools<81"
    # basic-pitch pulls TensorFlow, which crashes against numpy 2; without it the ONNX model is used
    "$UV" pip uninstall -q -p "$V/basicpitch/bin/python" tensorflow tensorflow-estimator \
        tensorflow-io-gcs-filesystem keras tensorboard || true
fi

"$V/audio/bin/python" -c "import zstandard" 2>/dev/null || "$UV" pip install -q -p "$V/audio/bin/python" zstandard   # fseq.py (render read-back) on an older env
"$V/audio/bin/python" -c "import torch, demucs, librosa, matplotlib, zstandard; print('audio env ok: torch', torch.__version__)"
"$V/basicpitch/bin/python" -c "import basic_pitch; print('basicpitch env ok')" 2>/dev/null
echo "environments ready in $V"
