# Use the official Python base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy all project files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Run Flask application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
