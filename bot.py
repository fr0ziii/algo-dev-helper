# --- Standard Library Imports ---
import os  # For accessing environment variables
import dotenv  # For loading variables from .env file

# --- Discord Imports ---
import discord  # Core discord.py library
from discord.ext import commands  # Bot commands extension

# --- Type Hinting Imports ---
from typing import Optional  # For type hinting optional return values

# --- Custom Module Imports ---
# These modules contain the specific logic for handling different types of user queries
from modules import network_info, qa_handler, doc_linker, algokit_handler

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
# Intents determine which events the bot receives from Discord.
# Without the correct intents, the bot won't receive certain events.
intents = discord.Intents.default()  # Start with default intents (presence, server members excluded)
intents.messages = True              # Need to receive message events (e.g., when a message is sent)
intents.message_content = True       # CRUCIAL: Need permission to read the *content* of messages.
                                     # This requires enabling the intent in the Discord Developer Portal.

# Initialize the bot client using commands.Bot
# commands.Bot is a subclass of discord.Client that adds command handling functionality.
# We pass the command prefix and the enabled intents.
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# --- Event Handlers ---
@bot.event
async def on_ready():
    """
    Called once when the bot is fully connected to Discord and ready to operate.
    This is typically used for setup tasks.
    """
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')
    # Pre-load data from files on startup.
    # This improves performance by avoiding file I/O on every message.
    # It assumes the data files don't change while the bot is running.
    print("Pre-loading data...")
    try:
        qa_handler.load_knowledge_base()
        print("  - Knowledge base loaded.")
        doc_linker.load_doc_links()
        print("  - Document links loaded.")
        algokit_handler.load_algokit_commands()
        print("  - AlgoKit commands loaded.")
        print("Data pre-loading complete.")
    except FileNotFoundError as e:
        print(f"Error loading data file: {e}. Please ensure all data files exist.")
        # Depending on severity, you might want to exit or disable features.
    except Exception as e:
        print(f"An unexpected error occurred during data loading: {e}")

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
        # Determine the user's intent based on keywords in their query and route
        # the request to the appropriate handler module.
        # The order of these 'if/elif' checks defines the priority:
        # 1. AlgoKit Command Help (most specific keywords)
        # 2. Documentation Link Request
        # 3. Network Status Request
        # 4. General Q&A (least specific, acts as a fallback)
        try:
            # --- Priority 1: AlgoKit Command Help Request ---
            print("[DEBUG] Checking AlgoKit Handler...") # DEBUG LOG
            algokit_keywords = ["algokit", "command"]
            known_commands = algokit_handler.load_algokit_commands().keys() # Get known commands
            # Check if query contains 'algokit', 'command', or a known command name
            if any(keyword in query_lower for keyword in algokit_keywords) or any(cmd in query_lower for cmd in known_commands):
                 print("[DEBUG] Attempting AlgoKit command lookup...") # DEBUG LOG
                 response = algokit_handler.get_algokit_help(query)
                 print(f"[DEBUG] AlgoKit handler response: {response}") # DEBUG LOG
                 # If response is still None here, it means keywords like 'algokit' might
                 # have matched, but no specific command was identified by the handler.
                 # We allow it to fall through to the next checks.

            # --- Priority 2: Documentation Link Request ---
            print(f"[DEBUG] Checking Docs Link... (response is None: {response is None})") # DEBUG LOG
            # Use 'elif' to ensure this only runs if the AlgoKit handler didn't provide a response.
            if response is None:
                doc_keywords = ["doc", "link for", "documentation", "url for"]
                # Check if query contains specific keywords indicating a doc link request
                if any(keyword in query_lower for keyword in doc_keywords):
                    print("[DEBUG] Attempting doc link lookup...") # DEBUG LOG
                    response = doc_linker.get_doc_link(query)
                    print(f"[DEBUG] Doc Linker response: {response}") # DEBUG LOG

            # --- Priority 3: Network Status Request ---
            print(f"[DEBUG] Checking Network Status... (response is None: {response is None})") # DEBUG LOG
            # Use 'elif' to ensure this only runs if previous handlers didn't respond.
            # Check for keywords related to network status.
            if response is None and ("round" in query_lower or "network status" in query_lower or "block" in query_lower):
                print("[DEBUG] Attempting network status lookup...") # DEBUG LOG
                # Determine preferred network (default to mainnet if not specified)
                network_pref = "testnet" if "testnet" in query_lower else "mainnet"
                response = await network_info.get_network_status_message(network_pref) # network_info is async
                print(f"[DEBUG] Network Status response: {response}") # DEBUG LOG

            # --- Priority 4: General Q&A Fallback ---
            print(f"[DEBUG] Checking Q&A... (response is None: {response is None}, query: '{query}')") # DEBUG LOG
            # This is the final fallback if no specific keywords were matched above.
            # Only attempt if the query is not empty (i.e., user typed something after the prefix).
            if response is None and query:
                print("[DEBUG] Attempting KB lookup...") # DEBUG LOG
                # Pass the original query (preserving case might be useful for some Q&A models/logic)
                response = qa_handler.get_answer_from_kb(query)
                print(f"[DEBUG] Q&A response: {response}") # DEBUG LOG

            # --- Handle Response / Fallback ---
            print(f"[DEBUG] Final response before sending: {response}") # DEBUG LOG

            # If any handler successfully generated a response string, send it.
            if response:
                await message.channel.send(response)
            # If no handler provided a response, but the user *did* type a query
            # (i.e., not just the prefix), send a helpful fallback message.
            elif query: # Check if query was non-empty after stripping prefix
                fallback_message = "Sorry, I couldn't find specific information for that query. Try asking differently, or check the Algorand Developer Portal: https://dev.algorand.co/"
                print(f"[DEBUG] No specific handler response for: '{query}'. Sending fallback.")
                await message.channel.send(fallback_message)
            # If the query was empty after the prefix (e.g., user typed just "!algohelp"),
            # we intentionally do nothing.

        except Exception as e:
            # General error handling for unexpected issues within the routing logic.
            print(f"Error processing message from {message.author.name}: {e}") # Log the error server-side.
            # Send a generic error message to the user to inform them something went wrong.
            await message.channel.send("An error occurred while processing your request. Please try again later.")

    # Note: commands.Bot has its own command processing. If we define commands
    # using @bot.command(), this on_message might interfere or be redundant
    # for those commands. For now, we stick to manual parsing in on_message.

# --- Run the Bot ---
# This is the standard Python entry point.
# The code inside this block will only run when the script is executed directly
# (not when it's imported as a module).
if __name__ == "__main__":
    print("Attempting to start the bot...")
    try:
        # Start the bot's connection to Discord using the token.
        # This is a blocking call, meaning the script will stay running here
        # listening for events until the bot is stopped (e.g., Ctrl+C).
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        # Handle the specific error when the token is invalid.
        print("\nError: Invalid Discord Bot Token.")
        print("Please check the DISCORD_BOT_TOKEN in your .env file and ensure it's correct.")
        print("Make sure you haven't accidentally revoked or regenerated the token.")
    except Exception as e:
        # Catch any other exceptions that might occur during bot startup.
        print(f"\nAn unexpected error occurred during bot startup: {e}")
