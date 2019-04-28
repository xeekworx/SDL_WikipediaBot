import discord
import requests
import re
from collections import OrderedDict 
from SDL_WikiParser import SDL_WikiParser

BOT_NAME = 'SDL_WikipediaBot'
BOT_VERSION = '1.0a'
BOT_TOKEN = 'NTcxMDcwOTAwOTk3MTkzNzQw.XMJNEw.FRT-EmZHUX6n5jpFLJ_HiwSwULY'
COMMAND_PREFIX = '!'
AUTHOR = "Xeek#8773"
AUTHOR_URL = "https://github.com/xeekworx/"
BOT_LOGO_URL = "https://xeek.xyz/sdl_wikibot_sm.png"
LIBSDLWIKI_URL = "https://wiki.libsdl.org/"
DISCORD_MSG_LIMIT = 2000
DISCORD_EMBED_FIELD_LIMIT = 1024
EMBED_COLOR = 0xf4c842

class SDL_WikipediaBotClient(discord.Client):
    async def on_ready(self):
        print(BOT_NAME + ' Version ' + BOT_VERSION + '\r\nWebsite: ' + AUTHOR_URL)
        print('─'*79)
        print('Logged on as {0}!'.format(self.user))

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
                return
            else:
                lastmsg = await message.channel.send("`Looking up {0}...`".format(query))

            # Generate the URLs for SDL's wiki site:
            url = self.create_wiki_url(query)
            url_for_display = self.create_wiki_url(query, False)
            wiki_content = self.download_wiki_page(url)

            # Delete the looking up message I sent earlier:
            await lastmsg.delete()

            if wiki_content is None or len(wiki_content) < 64:
                lastmsg = await message.channel.send(
                    "Beep Boop... Failed to find any wiki documents for **{0}**\r\n" + 
                    "*Do you take me for an idiot? Try again.*".format(query))
                await message.add_reaction('👎')
            else:
                await message.add_reaction('✅')

                parser = SDL_WikiParser(LIBSDLWIKI_URL)
                result = parser.parse(wiki_content, url_for_display)
                await self.output_embed(message, result, url_for_display)

    async def output_embed(self, message, parsed_result, url):
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
                if len(value) <= DISCORD_EMBED_FIELD_LIMIT:
                    embed.add_field(name=key.title(), value=value, inline=False)
                else:
                    embed.add_field(name=key.title(), value="This section was too powerful for discord, [Read more...]({0})".format(url + '#' + key.replace(' ', '_')), inline=False)

        # Rather than using the embed's footer, use a field with an empty title so that
        # the footer can have markdown (of which the footer doesn't support).
        embed.add_field(name='\u200B', value='⚙️ ' + BOT_NAME + '  |  Version  ' + BOT_VERSION + '  |  Author: **[{0}]({1})**'.format(AUTHOR, AUTHOR_URL), inline=False)

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

    def separator(self, length=32):
        return "{0}{1}{0}".format("\r\n", "▬"*length);


client = SDL_WikipediaBotClient()
client.run(BOT_TOKEN)
