import os
import dotenv
import discord
from discord.ext import commands # Import commands
from typing import Optional # Added for type hinting

# Import handlers from modules
from modules import network_info, qa_handler, doc_linker, algokit_handler # Added algokit_handler

# Load environment variables from .env file
# This allows sensitive info like the bot token to be kept out of version control
dotenv.load_dotenv()

# Get configuration from environment variables
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN') # The secret token for your Discord bot
BOT_PREFIX = os.getenv('BOT_PREFIX', '!algohelp ') # The prefix users type to invoke the bot

# --- Basic Input Validation ---
# Ensure the bot token is actually set
if not DISCORD_BOT_TOKEN:
    print("Error: DISCORD_BOT_TOKEN not found in .env file.")
    exit(1)

# --- Discord Bot Setup ---
# Define necessary intents for the bot to function
# Intents determine which events the bot receives from Discord
intents = discord.Intents.default() # Start with default intents
intents.messages = True             # Need to receive message events
intents.message_content = True      # CRUCIAL: Need permission to read message content

# Initialize the bot client using commands.Bot
# commands.Bot provides more features than discord.Client, including command handling
# We pass the prefix and the enabled intents
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# --- Event Handlers ---
@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')
    # Pre-load data on startup to avoid loading files on every message
    print("Loading knowledge base...")
    qa_handler.load_knowledge_base()
    print("Loading document links...")
    doc_linker.load_doc_links()
    print("Loading AlgoKit commands...")
    algokit_handler.load_algokit_commands() # Added loading algokit commands
    print("Data loaded.")

@bot.event
async def on_message(message: discord.Message): # Added type hint for clarity
    """Called when a message is sent to any channel the bot can see."""
    # 1. Ignore messages from the bot itself to prevent feedback loops
    if message.author == bot.user:
        return

    # 2. Check if the message starts with the defined prefix.
    #    We are manually checking the prefix here instead of using the
    #    commands.Bot command system for simplicity in this MVP phase.
    if message.content.startswith(BOT_PREFIX):
        # Extract the query part by removing the prefix and stripping whitespace
        query = message.content[len(BOT_PREFIX):].strip()
        query_lower = query.lower() # Use lowercase for case-insensitive matching
        print(f"Received query: '{query}' from {message.author.name}")

        response: Optional[str] = None # Initialize response variable with type hint

        # --- Routing Logic ---
        # Determine the user's intent and route to the appropriate handler.
        # The order of these checks defines the priority (AlgoKit > Docs > Network > Q&A).
        try:
            print("[DEBUG] Checking AlgoKit Handler...") # DEBUG LOG
            # Priority 1: AlgoKit Command Help Request
            algokit_keywords = ["algokit", "command"]
            known_commands = algokit_handler.load_algokit_commands().keys() # Get known commands
            # Check if query contains 'algokit', 'command', or a known command name
            if any(keyword in query_lower for keyword in algokit_keywords) or any(cmd in query_lower for cmd in known_commands):
                 print("[DEBUG] Attempting AlgoKit command lookup...") # DEBUG LOG
                 response = algokit_handler.get_algokit_help(query)
                 print(f"[DEBUG] AlgoKit handler response: {response}") # DEBUG LOG
                 # If response is still None here, it means keywords might have matched
                 # but no specific command was found by the handler. Let it fall through.

            # Priority 2: Documentation Link Request
            print(f"[DEBUG] Checking Docs Link... (response is None: {response is None})") # DEBUG LOG
            # Use ELIF to chain correctly only if AlgoKit handler didn't respond
            if response is None:
                doc_keywords = ["doc", "link for", "documentation", "url for"]
                # Check if query contains specific keywords indicating a doc link request
                if any(keyword in query_lower for keyword in doc_keywords):
                    print("[DEBUG] Attempting doc link lookup...") # DEBUG LOG
                    response = doc_linker.get_doc_link(query)
                    print(f"[DEBUG] Doc Linker response: {response}") # DEBUG LOG

            # Priority 3: Network Status Request
            print(f"[DEBUG] Checking Network Status... (response is None: {response is None})") # DEBUG LOG
            # Use ELIF to chain correctly only if previous handlers didn't respond
            if response is None and ("round" in query_lower or "network status" in query_lower or "block" in query_lower):
                print("[DEBUG] Attempting network status lookup...") # DEBUG LOG
                network_pref = "testnet" if "testnet" in query_lower else "mainnet"
                response = await network_info.get_network_status_message(network_pref) # network_info is async
                print(f"[DEBUG] Network Status response: {response}") # DEBUG LOG

            # Priority 4: General Q&A Fallback
            print(f"[DEBUG] Checking Q&A... (response is None: {response is None}, query: '{query}')") # DEBUG LOG
            # Use ELIF to chain correctly only if previous handlers didn't respond AND the query isn't empty
            if response is None and query:
                print("[DEBUG] Attempting KB lookup...") # DEBUG LOG
                response = qa_handler.get_answer_from_kb(query)
                print(f"[DEBUG] Q&A response: {response}") # DEBUG LOG

            # --- Handle Response / Fallback ---
            print(f"[DEBUG] Final response before sending: {response}") # DEBUG LOG
            # If any handler provided a response, send it
            if response:
                await message.channel.send(response)
            # Otherwise, if the query wasn't empty, send the fallback message
            elif query:
                fallback_message = "Sorry, I couldn't find specific information for that query. Try asking differently, or check the Algorand Developer Portal: https://dev.algorand.co/"
                print(f"[DEBUG] No specific handler response for: '{query}'. Sending fallback.")
                await message.channel.send(fallback_message)
            # If the query was empty after the prefix (e.g., just "!algohelp"), do nothing

        except Exception as e:
            # Catch-all for unexpected errors during processing
            print(f"Error processing message: {e}") # Log error to console
            # Optionally send a generic error message to the user in Discord
            await message.channel.send("An error occurred while processing your request. Please try again later.")

    # Note: commands.Bot has its own command processing. If we define commands
    # using @bot.command(), this on_message might interfere or be redundant
    # for those commands. For now, we stick to manual parsing in on_message.

# --- Run the Bot ---
# Standard Python entry point check
if __name__ == "__main__":
    print("Starting bot...")
    try:
        # Start the bot using the token from the environment variables
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        # Handle specific error for invalid token
        print("Error: Invalid Discord Bot Token. Please check your .env file.")
    except Exception as e:
        # Handle any other exceptions during bot startup
        print(f"An unexpected error occurred during startup: {e}")
