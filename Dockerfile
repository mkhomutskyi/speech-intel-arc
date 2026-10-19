FROM ubuntu:26.04
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /bin/uv
ENV DEBIAN_FRONTEND=noninteractive UV_PYTHON_INSTALL_DIR=/opt/python UV_LINK_MODE=copy
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates ffmpeg espeak-ng libgomp1 libze1 libze-intel-gpu1 intel-opencl-icd && rm -rf /var/lib/apt/lists/*
RUN uv python install 3.12 && uv venv --python 3.12 /opt/venv
ENV PATH=/opt/venv/bin:$PATH
RUN uv pip install --python /opt/venv/bin/python torch==2.14.0 --index-url https://download.pytorch.org/whl/xpu
RUN uv pip install --python /opt/venv/bin/python --extra-index-url https://storage.openvinotoolkit.org/simple/wheels/nightly --index-strategy unsafe-best-match openvino==2026.5.0.dev20261015 openvino-genai==2026.5.0.0.dev20261015 openvino-tokenizers==2026.5.0.0.dev20261015
RUN uv pip install --python /opt/venv/bin/python kokoro==0.9.4 misaki==0.9.4 fastapi==0.143.5 uvicorn==0.54.0 python-multipart==0.0.32 av==19.0.1 requests==2.34.2 numpy==2.5.4 transformers==5.20.1 huggingface-hub==2.2.0 && uv pip install --python /opt/venv/bin/python https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
COPY requirements.txt /tmp/requirements.txt
RUN uv pip install --python /opt/venv/bin/python -r /tmp/requirements.txt
COPY app/*.py /app/
RUN /opt/venv/bin/python /app/kokoro_alignment_fix.py
WORKDIR /app
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 SYCL_CACHE_PERSISTENT=1
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
