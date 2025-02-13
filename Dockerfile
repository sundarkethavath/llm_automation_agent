# Use the official Python image
FROM python:3.13

# Set the working directory in the container
WORKDIR /app

# Copy the application files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port FastAPI will run on
EXPOSE 8002

# Set the command to run the API
CMD ["uvicorn", "prompt:app", "--host", "127.0.0.1", "--port", "8002"]
