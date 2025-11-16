FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system dependencies (numpy/pandas build deps, tkinter for GUI, ssh)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
      gfortran \
      libopenblas-dev \
      libblas-dev \
      liblapack-dev \
      libx11-6 \
      python3-tk \
      tk \
      tcl \
      ca-certificates \
      ssh \
      locales \
      procps \
      libatlas3-base && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency list and install Python packages
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Copy application code
COPY . /app

# Create data directories (these are intended to be mounted from host)
RUN mkdir -p /app/Data /app/Merged /app/Archive

# Default command — launches the main app. If running headless for tasks, override command.
CMD ["python", "main.py"]