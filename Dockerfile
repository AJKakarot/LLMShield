# SentryGate - Phase 1 proof of concept.
#
# The models are baked into the image at build time, so `docker compose run poc`
# works with the network switched off. That matters: this is presented live.

FROM python:3.11-slim

# Torch pulls a lot; CPU-only keeps the image to ~1.5GB instead of ~6GB.
# MiniLM and deberta-base do not need a GPU, and the gateway will run CPU too.
RUN pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch==2.5.1 \
 && pip install --no-cache-dir sentence-transformers==3.3.1

ENV HF_HOME=/models \
    HF_HUB_DISABLE_PROGRESS_BARS=1 \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
    TRANSFORMERS_VERBOSITY=error \
    TOKENIZERS_PARALLELISM=false \
    PYTHONUNBUFFERED=1

# Pre-download both models into the image. Without this the container needs
# the internet on first run, which is exactly what we cannot rely on on stage.
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
from transformers import pipeline; \
SentenceTransformer('all-MiniLM-L6-v2'); \
pipeline('text-classification', model='protectai/deberta-v3-base-prompt-injection-v2', truncation=True); \
print('models cached')"

WORKDIR /app
COPY poc_bypass.py .

# No network needed from here on.
ENV HF_HUB_OFFLINE=1

ENTRYPOINT ["python", "poc_bypass.py"]
