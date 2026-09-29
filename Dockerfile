FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --gid 10001 jabfy \
    && useradd --create-home --uid 10001 --gid jabfy jabfy

COPY --from=jabfy-bus pyproject.toml README.md /jabfy-bus/
COPY --from=jabfy-bus jabfy_bus /jabfy-bus/jabfy_bus
COPY pyproject.toml README.md ./
COPY app ./app
COPY config ./config

# jabfy-bus is not published: build with `--build-context jabfy-bus=../jabfy-bus`.
RUN pip install --no-cache-dir "/jabfy-bus[mqtt]" .

USER jabfy

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

