# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Create a non-root user
RUN useradd -m spotify-stats

# Set the working directory to /code and change ownership
WORKDIR /code
RUN chown -R spotify-stats:spotify-stats /code

# Switch to the non-root user
USER spotify-stats

# Copy and install dependencies
COPY --chown=spotify-stats:spotify-stats ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt --user  # Install in user directory

# Copy application code
COPY --chown=spotify-stats:spotify-stats ./app /code/app

# Ensure user-installed packages are in PATH
ENV PATH="/home/spotify-stats/.local/bin:${PATH}"

# Expose the port
EXPOSE 9000

# Set the maintainer
LABEL maintainer="Jenslee Dsouza <dsouzajenslee@gmail.com>"

# Start Uvicorn with the root path
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000", "--proxy-headers", "--root-path", "/spotify-stats/api"]
