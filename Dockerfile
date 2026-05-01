# Use Python 3.11 Slim as base
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (chromium only to save space)
RUN python -m playwright install --with-deps chromium

# Copy the rest of the application
COPY . .

# Ensure the outputs directory exists
RUN mkdir -p outputs

# Expose port for Streamlit (Cloud Run uses 8080 by default)
EXPOSE 8080

# Command to run Streamlit
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port", "8080", "--server.address", "0.0.0.0"]
