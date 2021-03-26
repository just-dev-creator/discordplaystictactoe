import discord
import os
import gamestate
import pymongo
import datetime
import time

"""
You can invite this bot! 
Here's the link: https://discord.com/api/oauth2/authorize?client_id=811267001238159420&permissions=2112&scope=bot
It only requires the permissions of Sending Messages and Adding reactions. Use the following commands: &challenge <tag user> and &stats.
This project is licensed
Please read license information: license.txt
"""

token = os.environ['TOKEN']
playergrids = {}
userplayers = {}
opponents = {}
ingameplayer = []
prefix = "&"
mongoclient = None
mongodb = None
mongocollection = None


async def removePlayerFromLists(user):
    try:
        ingameplayer.remove(user)
        playergrids.pop(user)
        opponents.pop(user)
        playergrids.pop(user)
    except:
        print("There was an error by removing the player from the list. ")


def connectToMongoDB():
    global mongoclient
    global mongodb
    global mongocollection
    mongoclient = pymongo.MongoClient(os.environ["MONGODB_CONNECTION_STRING"])
    mongodb = mongoclient["discordplaysttt"]
    mongocollection = mongodb["userstats"]


def addStatsToDB(isLoseOrWin, user):
    if isLoseOrWin == "win":
        found = mongocollection.find_one({"userid": user.id})
        if found == None:
            mongocollection.insert_one({
                "userid": user.id,
                "wins": 1,
                "loses": 0
            })
        else:
            if not "wins" in found:
                newvalues = {"$set": {
                    "wins": 1
                }}
                mongocollection.update_one(found, newvalues)
            else:
                wins = found["wins"]
                wins += 1
                newvalues = {"$set": {
                    "wins": wins
                }}
                mongocollection.update_one(found, newvalues)
    elif isLoseOrWin == "lose":
        found = mongocollection.find_one({"userid": user.id})
        if found == None:
            mongocollection.insert_one({
                "userid": user.id,
                "wins": 0,
                "loses": 1
            })
        else:
            if not "loses" in found:
                newvalues = {"$set": {"loses": 1}}
                mongocollection.update_one(found, newvalues)
            else:
                loses = found["loses"]
                loses += 1
                newvalues = {"$set": {
                    "loses": loses
                }}
                mongocollection.update_one(found, newvalues)

    found = mongocollection.find_one({
        "userid": user.id
    })
    if found == None:
        mongocollection.insert_one({
            "playedgames": 1
        })
    else:
        if not "playedgames" in found:
            newvalues = {"$set": {
                "playedgames": 1
            }}
        else:
            played = found["playedgames"]
            played += 1
            newvalues = {"$set": {
                "playedgames": played
            }}
            mongocollection.update_one(found, newvalues)


def getStatsFromDB(isLoseOrWin, user):
    if isLoseOrWin == "win":
        found = mongocollection.find_one({"userid": user.id})
        if found == None or not "wins" in found:
            return 0
        return found["wins"]
    if isLoseOrWin == "lose":
        found = mongocollection.find_one({"userid": user.id})
        if found == None or not "loses" in found:
            return 0
        return found["loses"]


def isFull(grid):
    for i in grid.state:
        if i == 0:
            return False

    return True


async def sendGrid(grid, channel):
    message = ""
    for line in grid.getBoardForMessageAsList():
        message = message + line + "\n"

    if datetime.datetime.today().strftime('%Y-%m-%d') == "2021-02-18":
        message = message + "\n:nasa: Landen eines Rovers auf dem Mars heute ab 21.45 Uhr [hier](https://www.twitch.tv/nasa)"

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

async def sendFullInformation(channel, grid):
    await channel.send(channel.guild.get_member_named(
        f"{grid.player1.name}#{grid.player1.discriminator}").mention + " " + channel.guild.get_member_named(
        f"{grid.player2.name}#{grid.player2.discriminator}").mention + "\nNiemand hat gewonnen. Eure Statistiken werden nicht geändert!")
    addStatsToDB("none", channel.guild.get_member_named(f"{grid.player1.name}#{grid.player1.discriminator}"))
    addStatsToDB("none", channel.guild.get_member_named(f"{grid.player2.name}#{grid.player2.discriminator}"))
    await removePlayerFromLists(
        channel.guild.get_member_named(grid.player1.name + "#" + grid.player1.discriminator))
    await removePlayerFromLists(
        channel.guild.get_member_named(grid.player2.name + "#" + grid.player2.discriminator))
    return


async def makeTurn(cell, channel, member):
    if not member in ingameplayer:
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
    print("check for full")
    if isFull(grid) == True:
        await sendFullInformation(channel, grid)
    if not grid.turn(cell, active):
        await channel.send('Deine Auswahl konnte nicht ausgeführt werden!')
        await sendGrid(grid, channel)
        return False
    if grid.checkForWin(active):
        await channel.send(channel.guild.get_member_named(
            f"{grid.active.name}#{grid.active.discriminator}").mention + '\nYou win! Setze Board zurück!')
        if active == grid.player1:
            addStatsToDB("win", channel.guild.get_member_named(f"{active.name}#{active.discriminator}"))
            addStatsToDB("lose", channel.guild.get_member_named(f"{grid.player1.name}#{grid.player1.discriminator}"))
        else:
            addStatsToDB("win", channel.guild.get_member_named(f"{active.name}#{active.discriminator}"))
            addStatsToDB("lose", channel.guild.get_member_named(f"{grid.player2.name}#{grid.player2.discriminator}"))
        await removePlayerFromLists(
            channel.guild.get_member_named(grid.player1.name + "#" + grid.player1.discriminator))
        await removePlayerFromLists(
            channel.guild.get_member_named(grid.player2.name + "#" + grid.player2.discriminator))
        return False
    if isFull(grid):
        await sendFullInformation(channel, grid)

    if grid.active == grid.player1:
        grid.active = grid.player2
        await channel.send(channel.guild.get_member_named(
            grid.player2.name + "#" + grid.player2.discriminator).mention + ", du bist jetzt dran!")
    else:
        grid.active = grid.player1
        await channel.send(channel.guild.get_member_named(
            grid.player1.name + "#" + grid.player1.discriminator).mention + ", du bist jetzt dran!")
    await sendGrid(grid, channel)


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
            if (await makeTurn(1, message.channel, message.author)):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, message.channel)
        elif message.content == '2':
            if await makeTurn(2, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, message.channel)

        elif message.content == '3':
            if await makeTurn(3, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, message.channel)

        elif message.content == '4':
            if await makeTurn(4, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, message.channel)

        elif message.content == '5':
            if await makeTurn(5, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, message.channel)

        elif message.content == '6':
            if await makeTurn(6, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, message.channel)

        elif message.content == '7':
            if await makeTurn(7, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, message.channel)

        elif message.content == '8':
            if await makeTurn(8, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, message.channel)

        elif message.content == '9':
            if await makeTurn(9, message.channel, message.author):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, message.channel)

        elif message.content.startswith(prefix + "challenge"):
            args = message.content.split(" ")
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
                print(opponent)
                target = message.channel.guild.get_member(opponent)
                reac_mes = await message.channel.send(
                    target.mention + ", du wurdest von " + message.author.mention + " herausgefordert! Benutze die Reaktionen!")
                await reac_mes.add_reaction("✅")
                await reac_mes.add_reaction("✖")

        elif message.content == prefix + "stats":
            embed = discord.Embed(title=f"Statistiken für {message.author.name}#{message.author.discriminator}",
                                  colour=discord.Colour(0xa6f008), description="Folgend die Statistiken!",
                                  timestamp=datetime.datetime.utcfromtimestamp(time.time()))
            embed.set_footer(text="justCoding TicTacToe")
            embed.add_field(name="🏆",
                            value="Anzahl der gewonnen Runden: " + str(getStatsFromDB("win", message.author)))
            embed.add_field(name="💩",
                            value="Anzahl der verloreren Runden: " + str(getStatsFromDB("lose", message.author)))

            if getStatsFromDB("lose", message.author) == 0:
                embed.add_field(name="🔄",
                                value="Die K/D des Users beträgt: " + str(getStatsFromDB("win", message.author)))
            else:
                embed.add_field(name="🔄", value="Die K/D des Users beträgt: " + str(
                    getStatsFromDB("win", message.author) / getStatsFromDB("lose", message.author)))

            await message.channel.send(content=f"{user.mention}", embed=embed)

        elif message.content == "super_geheim":
            addStatsToDB("win", message.author)

    async def on_reaction_add(self, reaction, user):
        if user == self.user:
            return
        if reaction.emoji == "1️⃣":
            grid = None
            if "{}#{}".format(user.name, user.discriminator) in playergrids:
                grid = playergrids["{}#{}".format(user.name, user.discriminator)]
            elif user in opponents:
                grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
            if await makeTurn(1, reaction.message.channel, user):
                await sendGrid(grid, reaction.message.channel)
        elif reaction.emoji == "2️⃣":
            if await makeTurn(2, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, reaction.message.channel)
        elif reaction.emoji == "3️⃣":
            if await makeTurn(3, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, reaction.message.channel)
        elif reaction.emoji == "4️⃣":
            if await makeTurn(4, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, reaction.message.channel)
        elif reaction.emoji == "5️⃣":
            if await makeTurn(5, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, reaction.message.channel)
        elif reaction.emoji == "6️⃣":
            if await makeTurn(6, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, reaction.message.channel)
        elif reaction.emoji == "7️⃣":
            if await makeTurn(7, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, reaction.message.channel)
        elif reaction.emoji == "8️⃣":
            if await makeTurn(8, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, reaction.message.channel)
        elif reaction.emoji == "9️⃣":
            if await makeTurn(9, reaction.message.channel, user):
                grid = None
                if "{}#{}".format(user.name, user.discriminator) in playergrids:
                    grid = playergrids["{}#{}".format(user.name, user.discriminator)]
                elif user in opponents:
                    grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
                await sendGrid(grid, reaction.message.channel)
        elif reaction.emoji == "♻️":
            grid = None
            if "{}#{}".format(user.name, user.discriminator) in playergrids:
                grid = playergrids["{}#{}".format(user.name, user.discriminator)]
            elif user in opponents:
                grid = playergrids["{}#{}".format(opponents[user].name, opponents[user].discriminator)]
            if user == reaction.message.channel.guild.get_member_named(
                    grid.player1.name + "#" + grid.player1.discriminator):
                addStatsToDB("win", reaction.message.channel.guild.get_member_named(
                    grid.player2.name + "#" + grid.player2.discriminator))
                addStatsToDB("lose", user)
            else:
                addStatsToDB("win", reaction.message.channel.guild.get_member_named(
                    grid.player1.name + "#" + grid.player1.discriminator))
                addStatsToDB("lose", user)
            await removePlayerFromLists(
                reaction.message.channel.guild.get_member_named(grid.player1.name + "#" + grid.player1.discriminator))
            await removePlayerFromLists(
                reaction.message.channel.guild.get_member_named(grid.player2.name + "#" + grid.player2.discriminator))

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
                    user.mention + "\nDu kannst dich nicht selber herausfordern. Nutze vielleicht den irgendwann erscheinenden KI-Modus!")
                return

            if target in ingameplayer:
                await reaction.message.channel.send(
                    user.mention + "\nDer User, den du herausgefordert hast, ist bereits in einem Match!")
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
            await sendGrid(playergrids["{}#{}".format(user.name, user.discriminator)], reaction.message.channel)


connectToMongoDB()
intents = discord.Intents.default()
intents.members = True
client = DcClient(intents=intents)
client.run(token)
