FROM ubuntu:latest

# Install required dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sudo \
    python3 \
    python3-pip

# Download and install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy the Flask application
COPY flask_app.py .

# Expose the port on which the Flask app will run (default is 5000)
EXPOSE 5000

# Start the Ollama service in the background and run the Flask application
CMD ["sh", "-c", "ollama serve & python3 flask_app.py"]