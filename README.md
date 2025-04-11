# Meme Stealer Bot

A bot for automatically copying media content (memes) from Telegram channels to your own channel.

## Features

- Tracks new posts in specified source channels
- Copies only media files (images, videos, GIFs, etc.)
- Prevents content duplication using a hashing system
- Works in the background with minimal resource usage

## Requirements

- Python 3.7 or higher
- Telegram API keys (API_ID and API_HASH)
- Read access to source channels
- Publishing rights in the target channel

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Codyanka/meme-stealer.git
cd meme-stealer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following parameters:
```
API_ID=your_api_id
API_HASH=your_api_hash
SOURCE_CHANNELS=-100(IdChannel),-100(IdChannel)
TARGET_CHANNEL=-100(IdChannel)
CHECK_INTERVAL=30
```

## How to get setup data

### API_ID and API_HASH
1. Visit https://my.telegram.org/
2. Log in to your account
3. Go to "API development tools"
4. Create an application (name and other fields can be anything)
5. Copy API_ID and API_HASH

### Channel IDs
To get channel IDs:
1. Forward a message from the desired channel to @userinfobot
2. The bot will show the channel ID (usually a negative number)
3. Add the found IDs to the SOURCE_CHANNELS parameters (comma-separated) and TARGET_CHANNEL

## Running

```bash
python meme_stealer.py
```

For background execution (Linux/macOS):
```bash
nohup python meme_stealer.py &
```

## Stopping

The bot creates a `bot.pid` file with the process ID. To stop:
```bash
kill -9 $(cat bot.pid)
```

## Logs

Operation logs are saved to the `meme_stealer.log` file

## Notes

- The bot does not copy text messages without media
- On first run, the bot starts tracking only new messages
- Adjust CHECK_INTERVAL (in seconds) to change the frequency of channel checks

## How it works

The bot uses the Telethon library to interact with the Telegram API. It works in two modes:
1. Reacts to new messages in source channels in real-time
2. Periodically checks source channels in case something was missed

To prevent duplication, a hash is created for each message based on the text and media file ID.

## License

MIT 
