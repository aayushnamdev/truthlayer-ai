FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY truthlayer ./truthlayer
RUN pip install .
COPY . .
# Never bake secrets into the image: pass ANTHROPIC_API_KEY at run time (docker run -e ANTHROPIC_API_KEY ...).
RUN useradd --create-home app && chown -R app /app
USER app
EXPOSE 8501
ENV TRUTHLAYER_ROOT=/app
CMD ["streamlit", "run", "truthlayer/dashboard.py", "--server.address=0.0.0.0", "--server.port=8501", "--", "--root", "/app"]
