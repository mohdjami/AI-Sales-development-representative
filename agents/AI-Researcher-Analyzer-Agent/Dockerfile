# Use Python base image
FROM python:3.9-slim

# Install required system dependencies
# RUN apt-get update && apt-get install -y \
#     wget \
#     gnupg \
#     xvfb \
#     && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
#     && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
#     && apt-get update && apt-get install -y \
#     google-chrome-stable \
#     && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    chromium-driver \
    chromium \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 
    # && pip install --no-cache-dir undetected-chromedriver

# Copy application code
COPY . .

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]