import os
import dotenv
import discord
from discord.ext import commands # Import commands

# Import handlers from modules
from modules import network_info, qa_handler, doc_linker

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
    # Pre-load data handlers on startup
    print("Loading knowledge base...")
    qa_handler.load_knowledge_base()
    print("Loading document links...")
    doc_linker.load_doc_links()
    print("Data loaded.")

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
        query_lower = query.lower() # Use lowercase for matching intents
        print(f"Received query: '{query}' from {message.author.name}") # Log received query

        response = None # Initialize response variable

        # --- Routing Logic ---
        try:
            # Priority 1: Documentation Link Request
            doc_keywords = ["doc", "link for", "documentation", "url for"]
            if any(keyword in query_lower for keyword in doc_keywords):
                print(f"Attempting doc link lookup for: '{query}'")
                response = doc_linker.get_doc_link(query) # Pass original query if case matters for keywords in JSON keys

            # Priority 2: Network Status Request
            elif "round" in query_lower or "network status" in query_lower or "block" in query_lower:
                print(f"Attempting network status lookup for: '{query}'")
                network_pref = "testnet" if "testnet" in query_lower else "mainnet"
                response = await network_info.get_network_status_message(network_pref) # network_info is async

            # Priority 3: General Q&A Fallback
            elif query: # Check if query is not empty after stripping prefix
                print(f"Attempting KB lookup for: '{query}'")
                response = qa_handler.get_answer_from_kb(query)

            # --- Handle Response / Fallback ---
            if response:
                await message.channel.send(response)
            elif query: # Only send fallback if there was actually a query
                fallback_message = "Sorry, I couldn't find specific information for that query. Try asking differently, or check the Algorand Developer Portal: https://dev.algorand.co/"
                print(f"No specific handler response for: '{query}'. Sending fallback.")
                await message.channel.send(fallback_message)
            # If query was empty after prefix, do nothing

        except Exception as e:
            print(f"Error processing message: {e}") # Log error to console
            # Optionally send a generic error message to the user
            await message.channel.send("An error occurred while processing your request. Please try again later.")

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
