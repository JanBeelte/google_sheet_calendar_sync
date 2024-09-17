ARG IMAGE=python:3.12-alpine

FROM ${IMAGE} AS builder

RUN apk add --quiet --no-cache \
    build-base \
    libffi-dev \
    openssh \
    git \
    gcc

RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

RUN pip install poetry==1.8.0

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app/

# Actual project
COPY ./pyproject.toml ./poetry.lock ./
RUN touch README.md


RUN --mount=type=ssh poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# The runtime image, used to just run the code provided its virtual environment
FROM ${IMAGE} AS runtime

RUN apk --quiet --no-cache add ca-certificates libstdc++ \
    && rm -rf /var/cache/apk/*

WORKDIR /app/
ENV VIRTUAL_ENV=/app/.venv \
    PATH="${VIRTUAL_ENV}/bin:$PATH" \
    PYTHONPATH="$PYTHONPATH"

# COPY --from=builder /app/ /app/
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY google_sheet_calendar_sync/ /app/google_sheet_calendar_sync

RUN python -m compileall /app
CMD ["/app/.venv/bin/python", "-m", "google_sheet_calendar_sync.sync_sheet_to_calendar"]