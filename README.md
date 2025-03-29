<p align="center">
  <img src="algorand-logo.jpg" alt="Algorand Logo" width="400"/>
</p>

<h1 style="text-align:center;">AlgoDevHelper AI</h1>

## Introduction

AlgoDevHelper AI is an interactive Discord bot designed to be an indispensable, context-aware AI companion for Algorand developers. Born during the Algorand Developer Retreat hackathon, its purpose is to significantly accelerate the learning curve, streamline troubleshooting, and enhance the overall developer experience (DX) when building on Algorand, with a specific focus on leveraging the capabilities and best practices introduced with AlgoKit 3.0 and the revamped Developer Portal (`dev.algorand.co`).

It addresses the friction developers face due to information fragmentation, the learning curve of new tools, the need for quick recall/reference, accessing real-time network data, and navigating community channel noise, all directly within the Discord workflow.

## Status

**Under Development (Hackathon MVP)**

This project was initiated during the Algorand Developer Retreat hackathon (March 2025). It is currently focused on implementing the Minimum Viable Product (MVP) features outlined below.

## Features (MVP Goals)

The initial version aims to provide the following core functionalities:

*   **Knowledge-Based Q&A:** Answer questions about core Algorand concepts (ASA, ARC, TEAL, AVM, PPoS) and key AlgoKit 3.0 features based on the curated content from `dev.algorand.co/llms-small.txt`.
*   **Contextual Documentation Linking:** Provide accurate deep-links to relevant sections (Tutorials, How-Tos, Concepts, Reference) of the official Algorand Developer Portal (`dev.algorand.co`) based on user queries.
*   **AlgoKit 3.0 CLI Assistance:** Offer quick summaries and documentation links for core `algokit` commands (e.g., `init`, `bootstrap`, `compile`, `deploy`, `generate`).
*   **Real-Time Network Information:** Fetch and display the current consensus round for Algorand MainNet and TestNet upon request.
*   **Basic Interaction & Fallback:** Respond clearly to recognized commands and provide helpful fallback messages for unknown queries.

**Stretch Goals (Potential additions if time permits during the hackathon):**

*   Enhanced Q&A using a basic Hugging Face `transformers` pipeline.
*   Basic code snippets for common AlgoKit 3.0 tasks.
*   Simple conversational context (remembering the last topic).
*   Using Discord Embeds for cleaner responses.

## Technology Stack

*   **Language:** Python 3.9+
*   **Core Libraries:**
    *   `discord.py`: For Discord API interaction.
    *   `algosdk`: Official Algorand SDK for Python.
    *   `python-dotenv`: For managing environment variables.
    *   `requests`: For potential future HTTP requests.
*   **Data Format:** JSON (for structured mappings), Plain Text (for knowledge base).
*   **External APIs:** Discord API, AlgoNode API (MainNet/TestNet).

## Architecture Overview

The bot follows a modular architecture:

*   **`bot.py`:** Main application entry point, handles Discord events (`on_ready`, `on_message`), loads configuration, and routes requests.
*   **`modules/`:** Contains specialized Python modules for each core functionality (Q&A, Doc Linking, AlgoKit Help, Network Info).
*   **`data/`:** Stores the knowledge base (`llms-small.txt`) and curated mappings (`.json` files).
*   **`.env`:** File for storing configuration and secrets (API keys, bot token).

```mermaid
graph TD;
    A[User Message (Discord)] --> B(bot.py: on_message);
    B --> C{Parse & Route};
    C -- Q&A Query --> D[modules/qa_handler.py];
    C -- Doc Link Query --> E[modules/doc_linker.py];
    C -- AlgoKit Query --> F[modules/algokit_handler.py];
    C -- Network Query --> G[modules/network_info.py];
    C -- Snippet Query (Stretch) --> H[modules/code_snippets.py];
    C -- Unknown Query --> I[Fallback Message];

    D --> J[data/llms-small.txt];
    E --> K[data/new_doc_links.json];
    F --> L[data/algokit_commands.json];
    H --> M[data/snippets.json];

    G -- AlgoNode API Call --> N[algosdk];
    N --> O[AlgoNode (MainNet/TestNet)];

    J --> P[Response];
    K --> P;
    L --> P;
    M --> P;
    O -- Network Status --> G;
    G --> P;
    I --> P;

    P --> B;
    B -- Send Message --> A;

    subgraph Configuration
        direction LR
        Q[.env File] --> R[python-dotenv];
        R --> B;
    end

    style Configuration fill:#f9f,stroke:#333,stroke-width:2px;
    style J fill:#lightgrey,stroke:#333;
    style K fill:#lightgrey,stroke:#333;
    style L fill:#lightgrey,stroke:#333;
    style M fill:#lightgrey,stroke:#333;
    style O fill:#lightblue,stroke:#333;
```

## Setup & Installation

Follow these steps to set up the bot for local development:

1.  **Prerequisites:**
    *   Python 3.9 or later installed.
    *   Git installed.

2.  **Discord Bot Setup:**
    *   Go to the [Discord Developer Portal](https://discord.com/developers/applications).
    *   Create a **New Application**.
    *   Navigate to the **Bot** tab and click **Add Bot**.
    *   **Copy the Bot Token** and store it securely. You'll need it for the `.env` file.
    *   Enable the **Message Content Intent** under Privileged Gateway Intents.
    *   Note the **Application ID**.

3.  **Create a Test Server:**
    *   Create a private Discord server for testing.

4.  **Invite Bot to Server:**
    *   Go back to the Discord Developer Portal -> Your Application -> OAuth2 -> URL Generator.
    *   Select the following scopes: `bot`, `applications.commands`.
    *   Select the following Bot Permissions: `Read Messages/View Channels`, `Send Messages`, `Embed Links`, `Read Message History`.
    *   Copy the generated URL and paste it into your browser.
    *   Authorize the bot to join your test server.

5.  **Clone the Repository:**
    *   The repository will be hosted under the Algorand Developer Retreat GitHub Organization. (Link to be added once created).
    *   Clone the repository: `git clone [repository-url]`
    *   Navigate into the cloned directory: `cd [repository-name]`

6.  **Set Up Python Virtual Environment:**
    *   Create a virtual environment: `python -m venv .venv`
    *   Activate the environment:
        *   macOS/Linux: `source .venv/bin/activate`
        *   Windows (Git Bash): `source .venv/Scripts/activate`
        *   Windows (CMD/PowerShell): `.venv\Scripts\activate`

7.  **Install Dependencies:**
    *   `pip install -r requirements.txt`

8.  **Configure Environment Variables:**
    *   Create a file named `.env` in the project root directory.
    *   Add the following content, replacing placeholders with your actual values:
        ```dotenv
        # Discord Bot Token (Keep this secret!)
        DISCORD_BOT_TOKEN='YOUR_DISCORD_BOT_TOKEN_HERE'

        # AlgoNode API Endpoints
        ALGOD_MAINNET_URL='https://mainnet-api.algonode.cloud'
        ALGOD_TESTNET_URL='https://testnet-api.algonode.cloud'

        # Bot Command Prefix (Note the trailing space if desired)
        BOT_PREFIX='!algohelp '
        ```
    *   **Important:** Ensure `.env` is added to your `.gitignore` file to prevent committing secrets.

9.  **Set Up Data Directory:**
    *   Create a directory named `data` in the project root: `mkdir data`
    *   Download the knowledge base file: `curl https://dev.algorand.co/llms-small.txt -o data/llms-small.txt`
    *   Create empty JSON mapping files:
        *   `touch data/new_doc_links.json`
        *   `touch data/algokit_commands.json`
        *   (Optional for stretch goal) `touch data/snippets.json`

## Running the Bot Locally

1.  Ensure your virtual environment is activated (`source .venv/bin/activate` or equivalent).
2.  Run the bot script: `python bot.py`
3.  The console should indicate that the bot has connected successfully.

## Usage

Interact with the bot in your Discord server using either:

*   **Prefix:** Start your message with the defined `BOT_PREFIX` (e.g., `!algohelp `).
*   **Mention:** Mention the bot directly (`@AlgoDevHelperAI`).

**Example Queries:**

*   **Q&A:** `!algohelp what is an ASA?`
*   **Doc Link:** `!algohelp link for AlgoKit installation` or `!algohelp docs for TEALScript`
*   **AlgoKit Command:** `!algohelp algokit deploy command`
*   **Network Status:** `!algohelp mainnet round` or `!algohelp testnet status`

## Configuration

The following environment variables are configured in the `.env` file:

*   `DISCORD_BOT_TOKEN`: Your unique Discord bot token (required).
*   `ALGOD_MAINNET_URL`: The URL for the Algorand MainNet node API (defaults to AlgoNode).
*   `ALGOD_TESTNET_URL`: The URL for the Algorand TestNet node API (defaults to AlgoNode).
*   `BOT_PREFIX`: The string that triggers the bot commands (defaults to `!algohelp `).

## Contributing

This project is open source and contributions are welcome! As this project originated from a hackathon, the initial focus is on establishing the MVP.

Potential ways to contribute (post-hackathon):

*   Report bugs or suggest features by opening issues on the GitHub repository.
*   Help expand the knowledge base (`llms-*.txt`) coverage.
*   Curate more documentation links (`new_doc_links.json`).
*   Add more AlgoKit command details (`algokit_commands.json`).
*   Implement planned features or stretch goals.
*   Improve code quality, add tests, or enhance documentation.

Please follow the standard fork and pull request workflow for contributions.

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
