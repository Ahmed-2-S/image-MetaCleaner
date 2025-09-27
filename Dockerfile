FROM python:3.12-slim-bookworm

# Install exiftool (needed for metadata cleaning)
RUN apt-get update && apt-get install -y exiftool && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (better for Docker caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY . .

# Expose Flask port
EXPOSE 5000

# Flask config
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Run Flask
CMD ["flask", "run"]
