import os
import time
import json
import logging
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.sessions import StringSession
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("meme_stealer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')

SOURCE_CHANNELS = [int(channel_id) for channel_id in os.getenv('SOURCE_CHANNELS').split(',')]
TARGET_CHANNEL = int(os.getenv('TARGET_CHANNEL'))

CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 30))

POSTS_DB_FILE = 'copied_posts.json'

db_lock = asyncio.Lock()

client = TelegramClient(StringSession(), API_ID, API_HASH)

async def load_copied_posts():
    try:
        async with db_lock:
            with open(POSTS_DB_FILE, 'r') as f:
                return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_update": {}, "post_hashes": []}

async def save_copied_posts(data):
    async with db_lock:
        with open(POSTS_DB_FILE, 'w') as f:
            json.dump(data, f)

def get_message_hash(message):
    if hasattr(message, 'message') and message.message:
        text = message.message
    else:
        text = ""
    
    media_id = ""
    if message.media:
        if isinstance(message.media, MessageMediaPhoto):
            media_id = message.media.photo.id
        elif isinstance(message.media, MessageMediaDocument):
            media_id = message.media.document.id
    
    return f"{text}_{media_id}"

async def copy_media_post(message, target_channel):
    try:
        copied_posts = await load_copied_posts()
        message_hash = get_message_hash(message)
        
        if message_hash in copied_posts["post_hashes"]:
            logger.info(f"Post already copied (pre-send check), skipping: {message_hash[:30]}...")
            return False
        
        if message.media:
            if isinstance(message.media, MessageMediaPhoto):
                await client.send_file(target_channel, message.media.photo)
                logger.info(f"Copied photo to channel {target_channel}")
            elif isinstance(message.media, MessageMediaDocument):
                await client.send_file(target_channel, message.media.document)
                logger.info(f"Copied document/video/gif to channel {target_channel}")
            else:
                await client.send_file(target_channel, message.media)
                logger.info(f"Copied media to channel {target_channel}")
                
            copied_posts["post_hashes"].append(message_hash)
            await save_copied_posts(copied_posts)
            return True
        return False
    except Exception as e:
        logger.error(f"Error copying post: {e}")
        return False

async def check_new_posts():
    while True:
        try:
            copied_posts = await load_copied_posts()
            
            for channel_id in SOURCE_CHANNELS:
                if str(channel_id) not in copied_posts["last_update"]:
                    copied_posts["last_update"][str(channel_id)] = 0
            
            for source_channel in SOURCE_CHANNELS:
                messages = await client.get_messages(
                    source_channel, 
                    limit=10, 
                    min_id=int(copied_posts["last_update"].get(str(source_channel), 0))
                )
                
                if not messages:
                    continue
                
                copied_posts["last_update"][str(source_channel)] = max(
                    [msg.id for msg in messages] + 
                    [int(copied_posts["last_update"].get(str(source_channel), 0))]
                )
                
                await save_copied_posts(copied_posts)
                
                for message in reversed(messages):
                    if not message.media:
                        continue
                    
                    await copy_media_post(message, TARGET_CHANNEL)
                    
                    await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Error checking new posts: {e}")
        
        await asyncio.sleep(CHECK_INTERVAL)

def save_pid():
    with open('bot.pid', 'w') as f:
        f.write(str(os.getpid()))

async def main():
    save_pid()
    
    copied_posts = await load_copied_posts()
    logger.info("Getting current message IDs to track new posts...")
    
    for source_channel in SOURCE_CHANNELS:
        try:
            messages = await client.get_messages(source_channel, limit=1)
            if messages and len(messages) > 0:
                copied_posts["last_update"][str(source_channel)] = messages[0].id
                logger.info(f"Set starting point for channel {source_channel}: ID {messages[0].id}")
            else:
                copied_posts["last_update"][str(source_channel)] = 0
        except Exception as e:
            logger.error(f"Error getting last message for channel {source_channel}: {e}")
            copied_posts["last_update"][str(source_channel)] = 0
    
    await save_copied_posts(copied_posts)
    
    @client.on(events.NewMessage(chats=SOURCE_CHANNELS))
    async def new_message_handler(event):
        try:
            if not event.message.media:
                return
                
            await copy_media_post(event.message, TARGET_CHANNEL)
                
        except Exception as e:
            logger.error(f"Error processing new message: {e}")
    
    asyncio.create_task(check_new_posts())
    
    logger.info("Meme stealer started! Tracking only new memes without duplication.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
