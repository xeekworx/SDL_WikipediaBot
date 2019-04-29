import discord
import requests
import platform
import sys
from SDL_WikiParser import SDL_WikiParser
from SDL_WikiCache import SDL_WikiCache

BOT_NAME = 'SDL_WikipediaBot'
BOT_VERSION = '1.0a'
COMMAND_PREFIX = '!'
AUTHOR = "Xeek#8773"
AUTHOR_URL = "https://github.com/xeekworx/"
PROJECT_URL = "https://github.com/xeekworx/SDL_WikipediaBot"
BOT_LOGO_URL = "https://github.com/xeekworx/SDL_WikipediaBot/raw/master/images/sdl_wikibot.png"
LIBSDLWIKI_URL = "https://wiki.libsdl.org/"
CACHE_FILE = "wikicache.json"
CACHE_ENABLED = True
DISPLAY_PLATFORM = False
DISCORD_MSG_LIMIT = 2000
DISCORD_EMBED_FIELD_LIMIT = 1024
EMBED_COLOR = 0xf4c842

class SDL_WikipediaBotClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}'.format(self.user))

        print('Current Servers: ', end='')
        first = True
        async for guild in self.fetch_guilds():
            print(', ' if not first else '', end='')
            print(guild.name + ' ', end='')
            first = False

        self.cache = None
        try:
            self.cache = SDL_WikiCache(CACHE_FILE) if CACHE_ENABLED else None
        except:
            print("Warning: Failed to initialize cache.")

        print()
        await self.change_wiki_presence(False)

    async def on_message(self, message):
        if message.author == self.user:
            return
        elif message.content.startswith(COMMAND_PREFIX):
            parts = message.content.split()
            await self.on_command(message, parts[0], parts[1:])
            print('Message from {0.author}: {0.content}'.format(message))

    async def on_command(self, message, command, arguments):
        if command == str(COMMAND_PREFIX + "wiki"):
            await self.on_wiki(message, arguments)

    async def on_wiki(self, message, arguments):
        lastmsg = None

        if not arguments or len(arguments) < 1:
            lastmsg = await message.channel.send("You summoned me, but I need more information to do a lookup.")
            await message.add_reaction('🚽')
        else:
            query = arguments[0]
            param = arguments[1] if len(arguments) > 1 else None

            # Sanity check & lookup message:
            if len(arguments) > 1:
                lastmsg = await message.channel.send(
                    "You gave me more than one query and I'm way too lazy for that, so please wait while I only look up **{0}**...".format(query))
                await message.add_reaction('🚽')
            elif len(query) > 32:
                lastmsg = await message.channel.send(
                    "Beep boop, let me look up that really long word for you. Wait, screw that...\r\n" +
                    "*Who are you? Mary Poppins? That query is too long, is expialidocious one of yoru favorite words?*\r\n" + 
                    "Try this: **http://bfy.tw/NOLm**")
                await message.add_reaction('☂️')
            else:
                await self.change_wiki_presence(True)
                lastmsg = await message.channel.send("`Looking up {0}...`".format(query))

                # Generate the URLs for SDL's wiki site:
                url = self.create_wiki_url(query)
                url_for_display = self.create_wiki_url(query, False)

                # Try getting cached content or download live content if it's not in the cache.
                # Also update the cache if possible.
                async with message.channel.typing():
                    cached_content = None
                    try:
                        if self.cache and CACHE_ENABLED:
                            cached_content = self.cache.query(query)
                    except:
                        pass
                    if not cached_content:
                        wiki_content = self.download_wiki_page(url)

                # Delete the looking up message I sent earlier:
                await lastmsg.delete()

                if (not cached_content) and (wiki_content is None or len(wiki_content) < 64):
                    lastmsg = await message.channel.send(
                        "Beep Boop... Failed to find any wiki documents for **{0}**\r\n".format(query) + 
                        "*Do you take me for an idiot? Try again.*")
                    await message.add_reaction('👎')
                else:
                    await message.add_reaction('✅')

                    if not cached_content:
                        parser = SDL_WikiParser(LIBSDLWIKI_URL)
                        result = parser.parse(wiki_content, url_for_display)
                        from_cache = False
                        self.cache.update(key=query, data=result)
                        self.cache.save()
                    else:
                        result = cached_content # cached_content is pre-parsed
                        from_cache = True
                    await self.output_embed(message, result, url_for_display, from_cache)
                    await self.change_wiki_presence(False)

    async def output_embed(self, message, parsed_result, url, from_cache = False):
        # The first and second section of the output will be the title and description of
        # the embed.
        if 'Title' in parsed_result and 'Summary' in parsed_result:
            embed = discord.Embed(title="**" + parsed_result['Title'] + "**", description=parsed_result['Summary'], url=url, color=EMBED_COLOR)
        else:
            embed = discord.Embed(title="**N/A**", description="Something went wrong, there doesn't seem to be a title or summary to display", url=url, color=EMBED_COLOR)
        embed.set_thumbnail(url = BOT_LOGO_URL)

        # Add fields for every section, except for Title and Summary given above.
        for key, value in parsed_result.items(): 
            if key.lower() == 'title' or key.lower() == 'summary':
                continue
            else:
                if  not value or \
                    'You can add useful comments here' in value or \
                    'You can add your code example here' in value:
                    continue # There isn't anything in this section worth displaying
                elif len(value) <= DISCORD_EMBED_FIELD_LIMIT:
                    embed.add_field(name=key.title(), value=value, inline=False)
                else:
                    embed.add_field(name=key.title(), value="This section was too powerful for discord, [Read more...]({0})".format(url + '#' + key.replace(' ', '_')), inline=False)

        # Rather than using the embed's footer, use a field with an empty title so that
        # the footer can have markdown (of which the footer doesn't support).DISPLAY_PLATFORM
        last_field_value = '⚙️ **[{0}]({1})** | Version {2} | Author: **[{3}]({4})**'.format(BOT_NAME, PROJECT_URL, BOT_VERSION, AUTHOR, AUTHOR_URL)
        if DISPLAY_PLATFORM:
            last_field_value += '\r\nCurrent Platform: `{0} {1}`'.format(platform.system(), platform.release())
        embed.add_field(name='\u200B', value=last_field_value, inline=False)
        embed.set_footer(text="This content is live" if not from_cache else "This content is cached")

        # Send embed...
        await message.channel.send(embed=embed)

    def create_wiki_url(self, query, raw = True):
        query = query.replace(' ', '_')
        return "{0}{1}{2}".format(LIBSDLWIKI_URL, query, "?action=raw" if raw else '')

    def download_wiki_page(self, url):
        try:
            r = requests.get(url)
            return r.content
        except:
            return None

    async def change_wiki_presence(self, is_wiking = True):
        if is_wiking:
            game = discord.Game("with SDL's Wiki")
            await self.change_presence(status=discord.Status.online, activity=game)
        else:
            game = discord.Game("nothing right now")
            await self.change_presence(status=discord.Status.idle, activity=game)


def print_separator(length = 79):
    print('─'*length)

def main(argv):
    print(BOT_NAME + ' Version ' + BOT_VERSION + '\r\nWebsite: ' + AUTHOR_URL)
    print_separator()
    print('Current Platform: {0} {1}'.format(platform.system(), platform.release()))

    bot_token = None
    try:
        with open('token.txt', 'r') as f:
            bot_token = f.read()
    except:
        print()
        print("Exception trying to open or read the bot token from 'token.txt'!\r\n" +
              "1. Go to your Discord Applications Dashboard here: https://discordapp.com/developers/applications/\r\n" + 
              "2. Go to your app's page or generate a new application; then go to the bot section\r\n" +
              "3. Generate a Bot token and put it in 'token.txt' where this script will find it")
        return -1

    if bot_token:
        print("Token found, logging on...")
        client = SDL_WikipediaBotClient()
        client.run(bot_token.strip())

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))