# Quarter Master

A multi-agent system for securely managing `config.json` files for **Arma Reforger** game servers. Each Discord community can invite the bot to get a dedicated management dashboard for their server, allowing authorized members to monitor and modify backend settings directly from Discord.

## Overview

Quarter Master is a powerful tool for **Arma Reforger** communities. The concept is simple: each Discord community (guild) invites the bot and runs a lightweight agent on their game server (e.g., a VPS). The agent establishes a two-way connection with the bot, allowing for both real-time monitoring and remote management of the server's `config.json`.

This allows authorized community members to not only see their game server's backend status—including the mod list, server name, and player limit—but also to change these settings on the fly, all from the comfort of their own Discord.

It consists of two main components:

1.  **Agent:** A lightweight script that runs on a guild's game server. It securely reads the `config.json` file, sends it to the bot, and listens for commands to update the file locally.
2.  **Discord Management Dashboard:** The bot receives data from an agent and presents it in an interactive dashboard. Admins can use Discord commands to send updates back to the agent, which then modifies the server's configuration.

This empowers each community to independently monitor and manage their server from the convenience of their own Discord.

## Features

- **Remote Configuration:** Modify your Arma Reforger server's `config.json` using simple Discord commands.
- **Multi-Guild Support:** Designed to work independently and securely in any Discord server.
- **Dedicated Dashboards:** Each Discord server gets its own dashboard for its game server.
- **Real-time Sync:** The dashboard reflects the live server configuration, and changes made from Discord are applied instantly.
- **Secure Communication:** Agents authenticate with the bot to ensure data is sent to and received from the correct Discord server.
- **Easy to Deploy:** Simple setup for both the bot and the agent on your VPS or dedicated server.

## Architecture

The system is designed to be multi-tenant, allowing the bot to serve many different Discord communities without mixing them up.

-   **Discord Bot (Central Server):** A single bot that can be invited to any number of Discord servers. It exposes an API for agents, manages dashboards, and relays configuration changes from Discord admins to the appropriate agent.
-   **Agent (Client):** Deployed by a community's admin on their Arma Reforger server (VPS/dedicated machine). Each agent is configured with a unique key to securely communicate with the bot—sending its `config.json` for display and receiving updates to apply locally.

```
[Guild A's Discord] <=> Bot <=> Agent <=> [Guild A's Arma Server]
                           ^
                           |
[Guild B's Discord] <=> Bot <=> Agent <=> [Guild B's Arma Server]
```

## Getting Started

### Prerequisites

-   Python 3.10+
-   You must be an administrator of a Discord server and have administrative access to the game server (VPS or dedicated machine) you wish to manage.

### Installation & Usage

The process is split into two parts: setting up the bot on Discord and running the agent on your game server.

1.  **For Discord Server Admins:**
    -   Invite the Quarter Master bot to your Discord server using an admin account.
    -   Run a setup command (e.g., `/setup`) in a channel of your choice.
    -   The bot will create the management dashboard in that channel and provide a unique API Key for your server.
    -   Use Discord commands (e.g., `/set_server_name "My Awesome Server"`) to modify your game server's configuration.

2.  **For Game Server Admins:**
    -   Copy the `agent.py` script to your Arma Reforger server machine.
    -   Configure the agent with the bot's API endpoint and the unique API Key you received from the bot.
    -   Run the agent (e.g., `python3 agent.py`). It's recommended to run it as a background service.

Once the agent is running, it will establish a connection with the bot. The dashboard in your Discord server will come to life, and you will be able to manage your server's configuration directly from Discord.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue if you have ideas for improvements or find any bugs.

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature`).
6.  Open a pull request.

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.
