# Use an official Python runtime as a parent image
FROM python:3.11-slim


# Set the user to spotify-stats
RUN useradd -m spotify-stats
USER spotify-stats

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file
COPY --chown=spotify-stats:spotify-stats requirements.txt main.py ./

# Install the dependencies
RUN pip install -r requirements.txt

# Expose the port
EXPOSE 8000

# Set the maintainer
LABEL maintainer="Jenslee Dsouza <dsouzajenslee@gmail.com>"


# Run Uvicorn with workers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]