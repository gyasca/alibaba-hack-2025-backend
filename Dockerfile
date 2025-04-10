# Use Python base image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy files
COPY . .

# Install dependencies
RUN pip install --upgrade pip \
 && pip install -r alibabarequirements.txt

# Expose Flask port
EXPOSE 3001

# Run Flask
CMD ["python", "app.py"]
