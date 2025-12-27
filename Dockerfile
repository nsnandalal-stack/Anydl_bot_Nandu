FROM python:3.10-slim

# Install System Dependencies (FFmpeg for video, Aria2 for torrents)
RUN apt-get update && \
    apt-get install -y ffmpeg aria2 && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install Python Libraries
RUN pip install --no-cache-dir -r requirements.txt

# Run the Bot
CMD ["python", "bot.py"]
