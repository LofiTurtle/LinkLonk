from discord.ext import commands
import discord
from dotenv import load_dotenv
import os
import re

from dbutils import load_db, save_db

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(intents=intents)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        # Don't respond to own messages
        return

    db = load_db(message.guild)
    if not db['enabled']:
        return

    new_urls = convert_all_urls(message.content)

    if len(new_urls) == 0:
        # no urls to convert, so return early
        return

    # Suppress embeds on existing messages to remove rich link previews
    # this will remove all rich link previews, even from other sites if they're linked in the same message
    # but this is a limitation with the discord API
    await message.edit(suppress=True)

    current_url_batch: list[str] = []
    first_response = True
    for url in new_urls:
        if len(current_url_batch) < 5:
            # discord only embeds up to 5 links, so if there are more in a message, send response as multiple messages
            current_url_batch.append(url)
        else:
            # send batch of 5 messages
            response_message = ('Beep boop, embeds incoming\n' if first_response else '') + '\n'.join(
                current_url_batch)
            await message.reply(response_message, mention_author=False)
            first_response = False
            # clear the list batch and append next url
            current_url_batch = [url]

    if len(current_url_batch) > 0:
        # send any remaining messages
        response_message = (
            (f'Beep boop, embed{"s" if len(current_url_batch) > 1 else ""} incoming\n' if first_response else '')
            + '\n'.join(current_url_batch))
        await message.reply(response_message, mention_author=False)


def convert_all_urls(message_content: str) -> list[str]:
    new_urls: list[str] = []
    url_conversions: list[dict] = [{
            'url_pattern': r'https?://([\w\-]+\.)*tiktok\.com/([\w\-./?=&]+)',
            'new_domain': 'vxtiktok.com'
        },
        {
            'url_pattern': r'https?://([\w\-]+\.)*instagram\.com/([\w\-./?=&]+)',
            'new_domain': 'ddinstagram.com'
        },
        {
            'url_pattern': r'https?://([\w\-]+\.)*x\.com/([\w\-./?=&]+)',
            'new_domain': 'vxtwitter.com'
        },
        {
            'url_pattern': r'https?://([\w\-]+\.)*twitter\.com/([\w\-./?=&]+)',
            'new_domain': 'vxtwitter.com'
        }
    ]
    for url_conversion in url_conversions:
        new_urls.extend(convert_url(message_content=message_content, **url_conversion))

    return new_urls


def convert_url(message_content: str, url_pattern: str, new_domain: str) -> list[str]:
    urls = re.findall(url_pattern, message_content)
    new_urls: list[str] = []

    for subdomain, path, in urls:
        new_url = f'https://{subdomain}{new_domain}/{path}'
        new_urls.append(new_url)

    return new_urls


@bot.slash_command(name='enable', description='Enable automatic link conversion')
async def enable(ctx: discord.ext.commands.Context):
    db = load_db(ctx.guild)
    if db['enabled']:
        await ctx.respond('Link conversion already enabled', ephemeral=True)
    else:
        db['enabled'] = True
        save_db(ctx.guild, db)
        await ctx.respond('Link conversion enabled', ephemeral=True)


@bot.slash_command(name='disable', description='Disable automatic link conversion')
async def disable(ctx: discord.ext.commands.Context):
    db = load_db(ctx.guild)
    if not db['enabled']:
        await ctx.respond('Link conversion already disabled', ephemeral=True)
    else:
        db['enabled'] = False
        save_db(ctx.guild, db)
        await ctx.respond('Link conversion disabled', ephemeral=True)


bot.run(os.getenv('DISCORD_TOKEN'))
