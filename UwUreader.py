import discord
import sys
import random
sys.path.insert(0,"Dependencies/Nhentai-api")
from Nhentai_api import *
from datetime import datetime as dt
import json

TOKEN = ''
with open('credentials.json') as f:
    TOKEN = json.load(f)["token"]


client = discord.Client()

books = {}

prefix = "!"

class BookInstance:
    def __init__(self, book, message, page, last_interaction):
        self.book = book
        self.message = message
        self.page = page
        self.last_interaction = last_interaction
        self.msg = None

    def assign_msg(self, msg):
        self.msg = msg

    async def update_book(self, page):
        self.book.page = page
        self.page = page
        channel = client.get_channel(self.msg.channel.id)
        msg = await channel.fetch_message(self.msg.id)

        await update_message(msg, self)

    @staticmethod
    def get_latest_book_in_channel(channel_id):
        books_in_channel = []
        for bookId, book in books.items():
            if book.message.channel.id == channel_id:
                books_in_channel.append(book)

        if len(books_in_channel) > 0:
            books_in_channel.sort(key=lambda x: x.message.created_at, reverse=True)
            return books_in_channel[0]


def create_embed(instance, page_param=None):
    page = page_param if page_param is not None else instance.page
    embed = discord.Embed(title=instance.book.name,
                          description=(f"Page {page}" if page != 0 else "Cover"))
    embed.set_image(url=instance.book.get_image_link(page))
    return embed


async def update_message(msg, instance):
    await msg.edit(embed=create_embed(instance))


@client.event
async def on_raw_reaction_add(payload):
    global books

    if payload.message_id in books and client.user.id != payload.user_id:
        instance = books[payload.message_id]
        two_hours = 600

        if (dt.now() - instance.last_interaction).total_seconds() > two_hours:
            del books[payload.message_id]
            return

        instance.last_interaction = dt.now()
        if payload.emoji.id == 736745303650074666:
            instance.page += 1
            if instance.page > instance.book.page_count:
                instance.page = 0

        elif payload.emoji.id == 736745359614803989:
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

        await update_message(msg, instance)

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
    if message.content.startswith(prefix + 'view'):
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
            instance.assign_msg(msg)
            books[msg.id] = instance

            await msg.add_reaction(emoji="<:SixtenFarLeft:736745359614803989>")
            await msg.add_reaction(emoji="<:SixtenFarRight:736745303650074666>")

    elif message.content.startswith(prefix + "page"):
        book = BookInstance.get_latest_book_in_channel(message.channel.id)

        content = message.content.split()
        page = int(content[1])

        if page <= book.book.page_count:
            if page < 0:
                page = 0

            await book.update_book(page)

    elif message.content.startswith(prefix + "forward"):
        book = BookInstance.get_latest_book_in_channel(message.channel.id)

        content = message.content.split()
        page_delta = int(content[1])

        if page_delta + book.page > book.book.page_count:
            page_delta = book.book.page_count - book.page

        elif page_delta + book.page < 0:
            page_delta = book.page

        await book.update_book(book.page + page_delta)

    elif message.content.startswith(prefix + "back"):
        book = BookInstance.get_latest_book_in_channel(message.channel.id)

        content = message.content.split()
        page_delta = int(content[1])

        if book.page - page_delta > book.book.page_count:
            page_delta = -book.book.page_count - book.page

        elif book.page - page_delta < 0:
            page_delta = book.page

        await book.update_book(book.page - page_delta)

    elif message.content.startswith(prefix + "abort"):
        book = BookInstance.get_latest_book_in_channel(message.channel.id)

        await book.msg.delete()
        del books[book.msg.id]

    elif message.content.startswith(prefix + "random"):
        book_id = random.randint(0, 322223)
        book = Book(book_id)
        instance = BookInstance(book, message, 0, dt.now())

        if book.bad:
            await message.channel.send(f"There is no book with id {book_id}")

        else:
            msg = await message.channel.send(embed=create_embed(instance))
            instance.assign_msg(msg)
            books[msg.id] = instance

            await msg.add_reaction(emoji="<:SixtenFarLeft:736745359614803989>")
            await msg.add_reaction(emoji="<:SixtenFarRight:736745303650074666>")

    elif message.author.id == 217704901889884160 and message.content.startswith(prefix + 'clear'):
        await message.channel.purge(limit=100)




@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------\n\n')

client.run(TOKEN)