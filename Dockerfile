# Use Python 3.10 as the base image
FROM python:3.10.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first (to optimize caching)
COPY requirements.txt /app/

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of your application files
COPY . .

# Specify the command to run your script
CMD ["python", "main.py"]