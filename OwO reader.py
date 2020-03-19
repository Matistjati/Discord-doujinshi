import discord
from Nhentai_api import *
from datetime import datetime as dt
import json

TOKEN = ''
with open('credentials.json') as f:
    TOKEN = json.load(f)["token"]


client = discord.Client()

class BookInstance:
    def __init__(self, book, message, page, last_interaction):
        self.book = book
        self.message = message
        self.page = page
        self.last_interaction = last_interaction

books = {}

def create_embed(instance, page_param=None):
    page = page_param if page_param is not None else instance.page
    embed = discord.Embed(title=instance.book.name,
                          description=(f"Page {page}" if page != 0 else "Cover"))
    embed.set_image(url=instance.book.get_image_link(page))
    return embed

def update_message(msg, instance):
    msg.edit(embed=create_embed(instance))

@client.event
async def on_raw_reaction_add(payload):
    global books

    if payload.message_id in books and client.user.id != payload.user_id:
        instance = books[payload.message_id]
        two_hours = 7200

        if (dt.now() - instance.last_interaction).total_seconds() > two_hours:
            del d[payload.message_id]
            return

        instance.last_interaction = dt.now()
        if payload.emoji.id == 688534772078608384:
            instance.page += 1
            if instance.page > instance.book.page_count:
                instance.page = 0

        elif payload.emoji.id == 688534637076545536:
            instance.page -= 1
            if instance.page < 0:
                instance.page = instance.book.page_count

        print(instance.page)
        
        channel = client.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)

        reacts = msg.reactions
        for i in reacts:
                users = await i.users().flatten()
                for user in users:
                    if user != client.user:
                        await i.remove(user)
        
        update_message(msg, instance)
        
        #content= "Page " + str(instance.page),

        """future_load = instance.page + 2
        if future_load > instance.book.page_count:
            future_load = 0
        await load_empty(instance, future_load)"""

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself

    if message.author.id == client.user.id:
        return

    print(message)
    if message.content.startswith('!view'):
        content = message.content.split()
        bookId = int(content[1])
        page = 0
        if len(content) > 2:
            page = int(content[2])

        book = Book(bookId)
        instance = BookInstance(book, message, page, dt.now())

        if book.bad:
            await message.channel.send(f"There is no book with id {bookId}")
            
        else:
            msg = await message.channel.send(embed=create_embed(instance))
            books[msg.id] = instance

            await msg.add_reaction(emoji="<:left:688534637076545536>")
            await msg.add_reaction(emoji="<:right:688534772078608384>")

    elif message.author.id == 217704901889884160 and message.content.startswith('!clear'):
        await message.channel.purge(limit=100)

    


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------\n\n')

client.run(TOKEN)
