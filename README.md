# SDL_WikipediaBot
The Discord bot that displays SDL documentation using embed in the chat

**Prerequisites:**
- Python 3.6+ (I'm running it with Python 3.7 in Linux, but developing with 3.6 on Windows)

**Third-Party Dependencies:**
- discord.py
- requests

In order to start the bot, you'll have to go to the Discord applications dashboard, login to your Discord account, create an application, and then generate a token. This token needs to be in a file named "token.txt" in the current working directory for the bot so that it can load the token and connect. Obviously, you will not be able to add the bot to any Discord servers you do not have permission to add bots to.

The bot is currently being developed while on Windows 10, but I am running the bot regularly on Arch Linux as a systemd service.
