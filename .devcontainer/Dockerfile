FROM ghcr.io/astral-sh/uv:python3.12-bookworm

RUN apt-get update \
    && apt-get install -y gfortran \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
