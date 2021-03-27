import discord
import os
import gamestate
import pymongo
import datetime
import time
from discord_slash import SlashCommand, SlashContext
from dotenv import load_dotenv
import discord.ext

load_dotenv()

"""You can invite this bot! Here's the link: https://discord.com/api/oauth2/authorize?client_id=811267001238159420
&permissions=2112&scope=bot It only requires the permissions of Sending Messages and Adding reactions. Use the 
following commands: &challenge <tag user> and &stats. This project is licensed Please read license information: 
license.txt """

token = os.environ['TOKEN']
playergrids = {}
userplayers = {}
opponents = {}
ingameplayer = []
prefix = "&"
mongoclient = None
mongodb = None
mongocollection = None


async def remove_player_from_list(user):
    try:
        ingameplayer.remove(user)
        playergrids.pop(user)
        opponents.pop(user)
        playergrids.pop(user)
    except:
        print("There was an error by removing the player from the list. ")


def connect_to_mongodb():
    global mongoclient
    global mongodb
    global mongocollection
    mongoclient = pymongo.MongoClient(os.environ["MONGODB_CONNECTION_STRING"])
    mongodb = mongoclient["discordplaysttt"]
    mongocollection = mongodb["userstats"]


def add_stats_do_db(is_lose_or_win, user):
    if is_lose_or_win == "win":
        found = mongocollection.find_one({"userid": user.id})
        if found is None:
            mongocollection.insert_one({
                "userid": user.id,
                "wins": 1,
                "loses": 0
            })
        else:
            if "wins" not in found:
                new_values = {"$set": {
                    "wins": 1
                }}
                mongocollection.update_one(found, new_values)
            else:
                wins = found["wins"]
                wins += 1
                new_values = {"$set": {
                    "wins": wins
                }}
                mongocollection.update_one(found, new_values)
    elif is_lose_or_win == "lose":
        found = mongocollection.find_one({"userid": user.id})
        if found is None:
            mongocollection.insert_one({
                "userid": user.id,
                "wins": 0,
                "loses": 1
            })
        else:
            if "loses" not in found:
                new_values = {"$set": {"loses": 1}}
                mongocollection.update_one(found, new_values)
            else:
                loses = found["loses"]
                loses += 1
                new_values = {"$set": {
                    "loses": loses
                }}
                mongocollection.update_one(found, new_values)

    found = mongocollection.find_one({
        "userid": user.id
    })
    if found is None:
        mongocollection.insert_one({
            "playedgames": 1
        })
    else:
        if "playedgames" not in found:
            new_values = {"$set": {
                "playedgames": 1
            }}
        else:
            played = found["playedgames"]
            played += 1
            new_values = {"$set": {
                "playedgames": played
            }}
        mongocollection.update_one(found, new_values)


def get_stats_from_db(is_lose_or_win, user):
    if is_lose_or_win == "win":
        found = mongocollection.find_one({"userid": user.id})
        if found is None or "wins" not in found:
            return 0
        return found["wins"]
    if is_lose_or_win == "lose":
        found = mongocollection.find_one({"userid": user.id})
        if found is None or "loses" not in found:
            return 0
        return found["loses"]


def is_full(grid):
    for i in grid.state:
        if i == 0:
            return False

    return True


async def send_grid(grid, channel):
    message = ""
    for line in grid.getBoardForMessageAsList():
        message = message + line + "\n"

    lastmessage = await channel.send(message)
    await lastmessage.add_reaction("1️⃣")
    await lastmessage.add_reaction("2️⃣")
    await lastmessage.add_reaction("3️⃣")
    await lastmessage.add_reaction("4️⃣")
    await lastmessage.add_reaction("5️⃣")
    await lastmessage.add_reaction("6️⃣")
    await lastmessage.add_reaction("7️⃣")
    await lastmessage.add_reaction("8️⃣")
    await lastmessage.add_reaction("9️⃣")
    await lastmessage.add_reaction("♻️")


async def send_full_information(channel, grid):
    await channel.send(channel.guild.get_member_named(
        f"{grid.player1.name}#{grid.player1.discriminator}").mention + " " + channel.guild.get_member_named(
        f"{grid.player2.name}#{grid.player2.discriminator}").mention + "\nNiemand hat gewonnen. Eure Statistiken "
                                                                       "werden nicht geändert!")
    add_stats_do_db("none", channel.guild.get_member_named(f"{grid.player1.name}#{grid.player1.discriminator}"))
    add_stats_do_db("none", channel.guild.get_member_named(f"{grid.player2.name}#{grid.player2.discriminator}"))
    await remove_player_from_list(
        channel.guild.get_member_named(grid.player1.name + "#" + grid.player1.discriminator))
    await remove_player_from_list(
        channel.guild.get_member_named(grid.player2.name + "#" + grid.player2.discriminator))
    return


async def make_turn(cell, channel, member):
    if member not in ingameplayer:
        await channel.send(member.mention + "\nDu bist momentan in keinem Match!")
        return False
    cell = int(cell)
    cell -= 1
    grid = None
    if "{}#{}".format(member.name, member.discriminator) in playergrids:
        grid = playergrids["{}#{}".format(member.name, member.discriminator)]
    elif member in opponents:
        grid = playergrids["{}#{}".format(opponents[member].name, opponents[member].discriminator)]
    active = grid.active
    if member != channel.guild.get_member_named(grid.active.name + "#" + grid.active.discriminator):
        await channel.send(member.mention + "\nDu bist noch nicht dran!")
        return
    if is_full(grid):
        await send_full_information(channel, grid)
    if not grid.turn(cell, active):
        await channel.send('Deine Auswahl konnte nicht ausgeführt werden!')
        await send_grid(grid, channel)
        return False
    if grid.checkForWin(active):
        await channel.send(channel.guild.get_member_named(
            f"{grid.active.name}#{grid.active.discriminator}").mention + '\nYou win! Setze Board zurück!')
        if active == grid.player1:
            add_stats_do_db("win", channel.guild.get_member_named(f"{active.name}#{active.discriminator}"))
            add_stats_do_db("lose", channel.guild.get_member_named(f"{grid.player1.name}#{grid.player1.discriminator}"))
        else:
            add_stats_do_db("win", channel.guild.get_member_named(f"{active.name}#{active.discriminator}"))
            add_stats_do_db("lose", channel.guild.get_member_named(f"{grid.player2.name}#{grid.player2.discriminator}"))
        await remove_player_from_list(
            channel.guild.get_member_named(grid.player1.name + "#" + grid.player1.discriminator))
        await remove_player_from_list(
            channel.guild.get_member_named(grid.player2.name + "#" + grid.player2.discriminator))
        return False
    if is_full(grid):
        await send_full_information(channel, grid)

    if grid.active == grid.player1:
        grid.active = grid.player2
        await channel.send(channel.guild.get_member_named(
            grid.player2.name + "#" + grid.player2.discriminator).mention + ", du bist jetzt dran!")
    else:
        grid.active = grid.player1
        await channel.send(channel.guild.get_member_named(
            grid.player1.name + "#" + grid.player1.discriminator).mention + ", du bist jetzt dran!")
    await send_grid(grid, channel)


async def send_invite(args=None, ctx: SlashContext = None, message: discord.Message = None, user: discord.User = None):
    if ctx is None and message is None:
        raise Exception("One of the arguments must be specified!")
    elif message:
        if not args:
            raise Exception("When message is specified, args must be specified too.")
        # args = message.content.split(" ")
        if not len(args) == 2:
            await message.channel.send(message.author.mention + "\nDu hast keine Gegner angegeben!")
        else:
            opponent = (args[1].replace('<@', '').replace('>', ''))
            if "!" in opponent:
                opponent = opponent.replace('!', '')
            if "&" in opponent:
                await message.channel.send(
                    message.author.mention + "\nDu hast eine Rolle makiert! Dies ist nicht möglich!")
                return
            opponent = int(opponent)
            target = message.channel.guild.get_member(opponent)
            reac_mes = await message.channel.send(
                target.mention + ", du wurdest von " + message.author.mention + " herausgefordert! Benutze die Reaktionen!")
            await reac_mes.add_reaction("✅")
            await reac_mes.add_reaction("✖")
    elif ctx:
        if not user:
            raise Exception("When SlashContext is specified, user must be specified too.")
        reac_mes = await ctx.send(
            user.mention + ", du wurdest von " + ctx.author.mention + " herausgefordert! Benutze die Reaktionen!")
        await reac_mes.add_reaction("✅")
        await reac_mes.add_reaction("✖")


async def get_stats_embed(user: discord.User):
    embed = discord.Embed(title=f"Statistiken für {user.name}#{user.discriminator}",
                          colour=discord.Colour(0xa6f008), description="Folgend die Statistiken!",
                          timestamp=datetime.datetime.utcfromtimestamp(time.time()))
    embed.set_footer(text="justCoding TicTacToe")
    embed.add_field(name="🏆",
                    value="Anzahl der gewonnen Runden: " + str(get_stats_from_db("win", user)))
    embed.add_field(name="💩",
                    value="Anzahl der verloreren Runden: " + str(get_stats_from_db("lose", user)))

    if get_stats_from_db("lose", user) == 0:
        embed.add_field(name="🔄",
                        value="Die K/D des Users beträgt: " + str(get_stats_from_db("win", user)))
    else:
        embed.add_field(name="🔄", value="Die K/D des Users beträgt: " + str(
            get_stats_from_db("win", user) / get_stats_from_db("lose", user)))

    return embed

class DcClient(discord.Client):
    async def on_ready(self):
        print('Logged in as', self.user)
        await client.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name="jeglicher Zahl zwischen 1-9"))

    async def on_message(self, message):
        if message.author == self.user:
            return
        user = message.author
        if message.content == 'ping':
            await message.channel.send('Pong!')
        elif message.content == '1':
            if await make_turn(1, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, message.channel)
        elif message.content == '2':
            if await make_turn(2, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, message.channel)

        elif message.content == '3':
            if await make_turn(3, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, message.channel)

        elif message.content == '4':
            if await make_turn(4, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, message.channel)

        elif message.content == '5':
            if await make_turn(5, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, message.channel)

        elif message.content == '6':
            if await make_turn(6, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, message.channel)

        elif message.content == '7':
            if await make_turn(7, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, message.channel)

        elif message.content == '8':
            if await make_turn(8, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, message.channel)

        elif message.content == '9':
            if await make_turn(9, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, message.channel)

        elif message.content.startswith(prefix + "challenge"):
            args = message.content.split(" ")
            # if not len(args) == 2:
            #     await message.channel.send(message.author.mention + "\nDu hast keine Gegner angegeben!")
            # else:
            #     opponent = (args[1].replace('<@', '').replace('>', ''))
            #     if "!" in opponent:
            #         opponent = opponent.replace('!', '')
            #     if "&" in opponent:
            #         await message.channel.send(
            #             message.author.mention + "\nDu hast eine Rolle makiert! Dies ist nicht möglich!")
            #         return
            #     opponent = int(opponent)
            #     target = message.channel.guild.get_member(opponent)
            #     reac_mes = await message.channel.send(
            #         target.mention + ", du wurdest von " + message.author.mention + " herausgefordert! Benutze die Reaktionen!")
            #     await reac_mes.add_reaction("✅")
            #     await reac_mes.add_reaction("✖")
            await send_invite(args=args, message=message)

        elif message.content == prefix + "stats":
            # embed = discord.Embed(title=f"Statistiken für {message.author.name}#{message.author.discriminator}",
            #                       colour=discord.Colour(0xa6f008), description="Folgend die Statistiken!",
            #                       timestamp=datetime.datetime.utcfromtimestamp(time.time()))
            # embed.set_footer(text="justCoding TicTacToe")
            # embed.add_field(name="🏆",
            #                 value="Anzahl der gewonnen Runden: " + str(get_stats_from_db("win", message.author)))
            # embed.add_field(name="💩",
            #                 value="Anzahl der verloreren Runden: " + str(get_stats_from_db("lose", message.author)))
            #
            # if get_stats_from_db("lose", message.author) == 0:
            #     embed.add_field(name="🔄",
            #                     value="Die K/D des Users beträgt: " + str(get_stats_from_db("win", message.author)))
            # else:
            #     embed.add_field(name="🔄", value="Die K/D des Users beträgt: " + str(
            #         get_stats_from_db("win", message.author) / get_stats_from_db("lose", message.author)))

            await message.channel.send(content=f"{user.mention}", embed=await get_stats_embed(user))

        elif message.content == "super_geheim":
            add_stats_do_db("win", message.author)

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user == self.user:
            return
        print(reaction.emoji)
        if reaction.emoji == "♻️":
            grid = None
            if "{}#{}".format(user.name, user.discriminator) in playergrids:
                grid = playergrids["{}#{}".format(user.name, user.discriminator)]
            elif user in opponents:
                grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
            if user == reaction.message.channel.guild.get_member_named(
                    grid.player1.name + "#" + grid.player1.discriminator):
                add_stats_do_db("win", reaction.message.channel.guild.get_member_named(
                    grid.player2.name + "#" + grid.player2.discriminator))
                add_stats_do_db("lose", user)
                await reaction.message.channel.send(reaction.message.channel.guild.get_member_named(
                    grid.player2.name + "#" + grid.player2.discriminator).mention + "Du hast gewonnen, da " + user.mention + "aufgegeben hat!")
            else:
                add_stats_do_db("win", reaction.message.channel.guild.get_member_named(
                    grid.player1.name + "#" + grid.player1.discriminator))
                add_stats_do_db("lose", user)
                await reaction.message.channel.send(
                    reaction.message.channel.guild.get_member_named(
                        grid.player1.name + "#" + grid.player1.discriminator).mention + "Du hast gewonnen, da " + user.mention + " aufgegeben hat!")
            await remove_player_from_list(
                reaction.message.channel.guild.get_member_named(grid.player1.name + "#" + grid.player1.discriminator))
            await remove_player_from_list(
                reaction.message.channel.guild.get_member_named(grid.player2.name + "#" + grid.player2.discriminator))
        elif reaction.emoji == "1️⃣":
            grid = None
            if "{}#{}".format(user.name, user.discriminator) in playergrids:
                grid = playergrids["{}#{}".format(user.name, user.discriminator)]
            elif user in opponents:
                grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
            if await make_turn(1, reaction.message.channel, user):
                await send_grid(grid, reaction.message.channel)
        elif reaction.emoji == "2️⃣":
            if await make_turn(2, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, reaction.message.channel)
        elif reaction.emoji == "3️⃣":
            if await make_turn(3, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, reaction.message.channel)
        elif reaction.emoji == "4️⃣":
            if await make_turn(4, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, reaction.message.channel)
        elif reaction.emoji == "5️⃣":
            if await make_turn(5, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, reaction.message.channel)
        elif reaction.emoji == "6️⃣":
            if await make_turn(6, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, reaction.message.channel)
        elif reaction.emoji == "7️⃣":
            if await make_turn(7, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, reaction.message.channel)
        elif reaction.emoji == "8️⃣":
            if await make_turn(8, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, reaction.message.channel)
        elif reaction.emoji == "9️⃣":
            if await make_turn(9, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await send_grid(grid, reaction.message.channel)

        elif reaction.emoji == "✅":
            m = reaction.message.content.replace(', du wurdest von', '').replace(
                ' herausgefordert! Benutze die Reaktionen!', '')
            m_split = m.split(' ')
            m_mention = m_split[1]
            m_final = (m_mention.replace('<@', '').replace('>', ''))
            if "!" in m_final:
                m_final = m_final.replace('!', '')
            opponent = int(m_final)
            target = reaction.message.channel.guild.get_member(opponent)
            if target == user:
                await reaction.message.channel.send(
                    user.mention + "\nDu kannst dich nicht selber herausfordern. Nutze doch den KI-Modus(<https://bit.ly/3fiTwL5>).")
                return

            if target in ingameplayer:
                await reaction.message.channel.send(
                    user.mention + "\nDer User, den du herausgefordert hast, ist bereits in einem Match! Sollte dies ein Fehler sein, starte den Bot unter diesem Link neu: <<https://bit.ly/3fiTwL5>>")
                return

            userplayers.update({
                user: gamestate.Player(1, user.name, user.discriminator)
            })
            userplayers.update({
                target: gamestate.Player(-1, target.name, target.discriminator)
            })
            ingameplayer.append(user)
            ingameplayer.append(target)
            opponents.update({
                target: user
            })
            playergrids.update({
                "{}#{}".format(user.name, user.discriminator): gamestate.GameState(userplayers[user],
                                                                                   userplayers[target],
                                                                                   reaction.message.channel)
            })
            await send_grid(playergrids["{}#{}".format(user.name, user.discriminator)], reaction.message.channel)


connect_to_mongodb()
intents = discord.Intents.default()
intents.members = True
client = DcClient(intents=intents)
slash = SlashCommand(client, sync_commands=True)


@slash.slash(name="challenge", guild_ids=None, description="Fordere einen User zu einem Duell heraus!",
             options=[
                 {
                     "name": "opponent",
                     "description": "Specify the opponent you want to fight against",
                     "type": 6,
                     "required": True
                 }
             ])
async def _challenge(ctx: SlashContext, user: discord.User):
    await send_invite(ctx=ctx, user=user)


@slash.slash(name="stats", guild_ids=None, description="Zeige deine Statistiken an!", options=[
    {
        "name": "user",
        "description": "Der User, von dem du die Stats erhalten möchtest.",
        "type": 6,
        "required": False
    }
])
async def _stats(ctx: SlashContext, user: discord.User = None):
    if not user:
        await ctx.send(embed=await get_stats_embed(ctx.author))
    else:
        await ctx.send(embed=await get_stats_embed(user))



client.run(token)
