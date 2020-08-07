import discord
import json
import random
import sys
from datetime import datetime as dt
sys.path.insert(0, "Dependencies/Nhentai-api")
from Nhentai_api import *


TOKEN = ''

on_heroku = False
if 'token' in os.environ:
    on_heroku = True
    TOKEN = os.environ['token']
  
else:
    with open('credentials.json') as f:
        TOKEN = json.load(f)["token"]


client = discord.Client()

books = {}

prefix = "!"

hen_ties = random.shuffle(
    [
        "https://cdn.discordapp.com/attachments/739847584545505402/739847622776455249/Hen-tie.jpg",
        "https://cdn.discordapp.com/attachments/739847584545505402/739850739366494218/Thicken.png",
        "https://cdn.discordapp.com/attachments/739847584545505402/739850752629145680/Pain_chicken.jpg",
        "https://cdn.discordapp.com/attachments/739847584545505402/739850997202944081/Chicken_wander.png",
        "https://cdn.discordapp.com/attachments/739847584545505402/739851007156027392/Long_boi_chicken.png",
        "https://cdn.discordapp.com/attachments/739847584545505402/739851258512277575/Trapp.png",
        "https://cdn.discordapp.com/attachments/739847584545505402/739851609529647154/Hen_tie_2.jpg",
        "https://cdn.discordapp.com/attachments/739847584545505402/739851610410450954/Motherclucker.png",
        "https://cdn.discordapp.com/attachments/739847584545505402/739854897889148989/Nice_cock.png",
        "https://cdn.discordapp.com/attachments/739847584545505402/739855614662017024/Black_cock.png",
        "https://cdn.discordapp.com/attachments/739847584545505402/739860912080420955/Kdc.png",
    ])

hen_tie_index = 0


class BookInstance:
    def __init__(self, book, message, page, last_interaction):
        self.book = book
        self.page_count = book.page_count
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
        for book_id, book in books.items():
            if book.message.channel.id == channel_id:
                books_in_channel.append(book)

        if len(books_in_channel) > 0:
            books_in_channel.sort(key=lambda x: x.message.created_at, reverse=True)
            return books_in_channel[0]


def create_embed(instance, page_param=None):
    page = page_param if page_param is not None else instance.page
    embed = discord.Embed(title=f"{instance.book.name} ({instance.book.book_id}){ ' Posted for debug' if not on_heroku else ''}",
                          description=(f"Page {page}" if page != 0 else "Cover"))
    embed.set_image(url=instance.book.get_image_link(page))
    return embed


async def update_message(msg, instance):
    await msg.edit(embed=create_embed(instance))


@client.event
async def on_raw_reaction_add(payload):
    global books

    if client.user.id == payload.user_id:
        return

    channel = client.get_channel(payload.channel_id)
    msg = await channel.fetch_message(payload.message_id)

    ten_minutes = 600

    if (dt.utcnow() - msg.created_at).total_seconds() < ten_minutes:
        if payload.emoji == discord.PartialEmoji(name="❌"):
            await msg.delete()
        elif payload.message_id in books and (payload.emoji.id == 736745303650074666 or payload.emoji.id == 736745359614803989):
            instance = books[payload.message_id]

            instance.last_interaction = dt.now()
            if payload.emoji.id == 736745303650074666:
                instance.page += 1
                if instance.page > instance.book.page_count:
                    instance.page = 0

            elif payload.emoji.id == 736745359614803989:
                instance.page -= 1
                if instance.page < 0:
                    instance.page = instance.book.page_count

            reacts = msg.reactions
            for i in reacts:
                users = await i.users().flatten()
                for user in users:
                    if user != client.user:
                        await i.remove(user)

            await update_message(msg, instance)

            """future_load = instance.page + 2
            if future_load > instance.book.page_count:
                future_load = 0
            await load_empty(instance, future_load)"""


@client.event
async def on_message(message):
    # we do not want the bot to reply to itself

    if message.author.id == client.user.id:
        return

    if message.content.startswith(prefix + 'view'):
        content = message.content.split()
        book_id = int(content[1])
        page = 0
        if len(content) > 2:
            page = int(content[2])

        book = Book(book_id)
        instance = BookInstance(book, message, page, dt.now())

        if book.bad:
            await message.channel.send(f"There is no book with id {book_id}")

        else:
            msg = await message.channel.send(embed=create_embed(instance))
            instance.assign_msg(msg)
            books[msg.id] = instance

            await msg.add_reaction(emoji="<:SixtenFarLeft:736745359614803989>")
            await msg.add_reaction(emoji="<:SixtenFarRight:736745303650074666>")
            await msg.add_reaction(emoji="❌")

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

    elif message.content.startswith(prefix + "beginning"):
        book = BookInstance.get_latest_book_in_channel(message.channel.id)

        await book.update_book(0)

    elif message.content.startswith(prefix + "end"):
        book = BookInstance.get_latest_book_in_channel(message.channel.id)

        await book.update_book(book.page_count)

    elif message.content.startswith(prefix + "abort"):
        book = BookInstance.get_latest_book_in_channel(message.channel.id)

        await book.msg.delete()
        del books[book.msg.id]

    elif message.content.startswith(prefix + "random_image"):
        split_content = message.content.split()
        amount = 1
        query = " "
        if len(split_content) > 1:
            if split_content[1].isdigit():
                amount = int(split_content[1])

                query = " ".join(split_content[2:])
            else:
                query = " ".join(split_content[1:])





        book_query = Search(query)
        for i in range(amount):
            page = random.randint(1, book_query.page_amount)
            book_query.go_to_page(page)

            result = book_query.result

            book_id = random.choice(result)["id"]

            book = Book(book_id)

            instance = BookInstance(book, message, random.randint(0, book.page_count), dt.now())
            msg = await message.channel.send(embed=create_embed(instance))
            await msg.add_reaction(emoji="❌")

    elif message.content.startswith(prefix + "random"):
        split_content = message.content.split()
        if "," in message.content:
            content = " ".join(message.content.split()[1:])
            content = content.split(",")
            for i in range(len(content)):
                content[i] = content[i].strip()

            query = ""
            include = [i for i in content if not i.startswith("-")]
            exclude = [i for i in content if i.startswith("-")]
            if len(include) > 0:
                query += "tag:"
                for i in include:
                    query += f"\"{i}\" "

            if len(exclude) > 0:
                query += " -tag:"
                for i in exclude:
                    query += f"\"{i[1:]}\" "

        elif len(split_content) > 1:
            content = split_content[1:]

            query = " ".join(content)
        else:
            query = " "

        book_query = Search(query)

        if len(book_query.result) == 0:
            global hen_tie_index

            embed = discord.Embed(title="Nobody here but us chickens!")
            embed.set_image(url=hen_ties[hen_tie_index])
            hen_tie_index += 1
            if hen_tie_index == len(hen_ties):
                hen_tie_index = 0
                random.shuffle(hen_ties)
            await message.channel.send(embed=embed)
            return

        page = random.randint(1, book_query.page_amount)
        if page != 1:
            book_query.go_to_page(page)

        result = book_query.result

        book_id = random.choice(result)["id"]

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
            await msg.add_reaction(emoji="❌")


    elif message.content.startswith(prefix + "help"):
        embed = discord.Embed(title="Commands",
                              description=(f"""**!view <id>**: start reading a doujinshi
                              **!page <page>**: goes to a certain page
                              **!forward <pages>**: goes forward some pages
                              **!back <pages>**: goes back some pages
                              **!beginning**: go to the first page
                              **!end**: go to the last page
                              **!abort**: remove the last started doujinshi
                              **!random**: start readinga a random doujinshi
                              **!random <search>**: Read a random doujinshi from a search result
                              **!random <tags>**: Display a random doujinshi with certain tags. Comma separate them, and start off with - to exclude. Example: !random yuri, kantai collection, -netorare
                              """))
        await message.channel.send(embed=embed)

    elif message.author.id == 217704901889884160 and message.content.startswith(prefix + 'clear'):
        content = message.content.split(" ")
        limit = 100
        if len(content) > 1:
            limit = int(content[1]) + 1
        await message.channel.purge(limit=limit)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------\n\n')

client.run(TOKEN)
