# Spotify Stats
Welcome to the Spotify Stats API! 🎶

This API serves as a glorified caching service that allows you to efficiently fetch and store your top tracks and genres from Last.fm, leveraging the power of Spotify and Last.fm data.

## Features
- **Caching Support**: Utilizes Redis to cache responses for improved performance and reduced API calls.
- **Retrieve Your Top Tracks**: Access your most listened tracks effortlessly.
- **Fetch Your Top Genres**: Discover the genres you listen to the most.

## Getting Started
To get started, clone the repository and set up your environment variables as specified in the `.env` file.

## API Endpoints
- **GET /spotify-stats/api/top-tracks**: Get your top tracks.
- **GET /spotify-stats/api/top-genres**: Get your top genres.
- **GET /ping**: Check the health of the API.

## Requirements
- Python 3.11
- Redis

## Installation
1. Clone the repository.
2. Install the required packages using `pip install -r requirements.txt`.
3. Run the application using `uvicorn app.main:app --host 0.0.0.0 --port 9000`.

## License
This project is licensed under the MIT License.

Happy listening! 🎧
