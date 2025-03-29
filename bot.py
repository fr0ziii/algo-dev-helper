import os
import dotenv
import discord
from discord.ext import commands # Import commands

# Import handlers from modules
from modules import network_info

# Load environment variables from .env file
dotenv.load_dotenv()

# Get configuration from environment variables
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
BOT_PREFIX = os.getenv('BOT_PREFIX', '!algohelp ') # Default prefix if not set

# --- Basic Input Validation ---
if not DISCORD_BOT_TOKEN:
    print("Error: DISCORD_BOT_TOKEN not found in .env file.")
    exit(1)

# --- Discord Bot Setup ---
# Define necessary intents
# MESSAGE_CONTENT is crucial for reading message content after prefix/mention
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True # Enable the Message Content intent

# Initialize the bot client
# Using commands.Bot for broader compatibility and command handling features
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents) # Use command_prefix here

# --- Event Handlers ---
@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')
    # TODO: Potentially load data handlers here

@bot.event
async def on_message(message):
    """Called when a message is sent to any channel the bot can see."""
    # 1. Ignore messages from the bot itself to prevent loops
    if message.author == bot.user:
        return

    # 2. Check if the message starts with the defined prefix
    # Since we are using commands.Bot, we could use the command system,
    # but for this phase, we'll keep the manual prefix check for simplicity.
    if message.content.startswith(BOT_PREFIX):
        # Extract the query part after the prefix
        query = message.content[len(BOT_PREFIX):].strip()
        print(f"Received command: '{query}' from {message.author.name}") # Log received command

        # --- Manual Routing Logic (as commands.Bot processes commands differently) ---
        if query.lower() == "hello":
            await message.channel.send(f"Hello {message.author.mention}!")
        elif query.lower() == "ping":
            await message.channel.send("Pong!")
        # Add network status command
        elif "round" in query.lower() or "network status" in query.lower():
            # Determine network preference (default to mainnet)
            network_pref = "testnet" if "testnet" in query.lower() else "mainnet"
            status_message = await network_info.get_network_status_message(network_pref)
            await message.channel.send(status_message)
        else:
            # Placeholder for unrecognised command or fallback to QA
            await message.channel.send(f"Command '{query}' received, but not yet implemented.")

    # Note: commands.Bot has its own command processing. If we define commands
    # using @bot.command(), this on_message might interfere or be redundant
    # for those commands. For now, we stick to manual parsing in on_message.

# --- Run the Bot ---
if __name__ == "__main__":
    print("Starting bot...")
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        print("Error: Invalid Discord Bot Token. Please check your .env file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
