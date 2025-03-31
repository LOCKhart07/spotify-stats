# Spotify Stats
Welcome to the Spotify Stats API! 🎶

This API serves as a glorified caching service that allows you to efficiently fetch and store your top tracks and artists from Spotify, with built-in caching for improved performance.

## Features
- **Caching Support**: Utilizes Redis to cache responses for improved performance and reduced API calls.
- **Retrieve Your Top Tracks**: Access your most listened tracks with details like name, artist, and album artwork.
- **Fetch Your Top Artists**: Discover your favorite artists with their genres and profile images.
- **Rate Limiting**: Built-in protection against excessive API calls.
- **Input Validation**: Ensures all parameters are within valid ranges.
- **Error Handling**: Comprehensive error handling with detailed error messages.
- **Logging**: Detailed logging for better debugging and monitoring.

## Getting Started
To get started, clone the repository and set up your environment variables as specified in the `.env` file.

## API Endpoints
- **GET /spotify-stats/api/top-tracks**: Get your top tracks
  - Parameters:
    - `limit` (1-50, default: 10): Number of tracks to return
    - `page` (≥1, default: 1): Page number for pagination
    - `time_range` (short_term|medium_term|long_term, default: short_term): Time range for the data
- **GET /spotify-stats/api/top-artists**: Get your top artists
  - Parameters:
    - `limit` (1-50, default: 10): Number of artists to return
    - `page` (≥1, default: 1): Page number for pagination
    - `time_range` (short_term|medium_term|long_term, default: short_term): Time range for the data
- **GET /ping**: Check the health of the API

## Requirements
- Python 3.11
- Redis

## Installation
1. Clone the repository.
2. Install the required packages using `pip install -r requirements.txt`.
3. Run the application using `uvicorn app.main:app --host 0.0.0.0 --port 9000`.

## Environment Variables
Create a `.env` file with the following variables:
```
SPOTIFY_REFRESH_TOKEN=your_refresh_token
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
BEARER_TOKEN=your_bearer_token
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_TTL=86400
```

## License
This project is licensed under the MIT License.

Happy listening! 🎧
