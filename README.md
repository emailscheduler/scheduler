# Meeting Scheduler

## Overview
This Python script extracts and manages meeting requests from email using OpenAI's API.

## Features
- Authenticates with Gmail API to read and modify emails
- Uses OpenAI to extract structured meeting details from email content
- Supports Google Calendar API for scheduling meetings 

## Requirements
- Python 3.8+
- Google API Client Libraries
- OpenAI API Key
- Required Python dependencies (see Installation section)

## Installation
1. Clone this repository:
   ```sh
   git clone https://github.com/emailscheduler/scheduler.git
   cd scheduler
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set up authentication:
   - Obtain `credentials.json` from Google Cloud Console.
   - Place it in the project directory.
   - Run the script to generate `token.json` for authentication.
   - Note: `token.json` needs to be deleted and regenerated after each scope change

## Usage
Run the script to authenticate and process emails:
```sh
python main.py "<YOUR NAME HERE>"
```

## Testing
Run unit tests with:
```sh
python -m unittest discover tests
```

## Configuration
Set your OpenAI API key as an environment variable:
```sh
export OPENAI_API_KEY='<YOUR API KEY HERE>'
```

