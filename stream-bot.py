### imports ###

import discord
import asyncio
from twitchAPI.twitch import Twitch
from discord.ext import commands
import json
import os
import datetime

### token and important vars ###

bot_token = '' # < put your discord token here

### vvv for twitch notis ###
twitch_client_id = '' # < twitch client id
twich_client_secret = '' # < twitch client secret
live_channel_id = None # < id of live channel goes here
twitch_username = '' # < twitch username you want to send
### ^^^ for twitch notis ###

### paths ###

base_dir = os.path.dirname(os.path.abspath(__file__)) # gets file dir
settings_file = os.path.join(base_dir, "settings.json") # file dir + settings.json
logs_file = os.path.join(base_dir, "logs.json") # file dir + logs.json

### intents ###

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

### defs bot ###
                 # put the id of owner here vvv
bot = discord.Bot(intents=intents, owner_id=None)

### defs twitch ###

twitch = Twitch(twitch_client_id, twich_client_secret)

### vars ###

tse = False # enbales and disables twitch checking for live streams

### role req ###

def role_required(role_name):
    def predicate(ctx):
        with open(settings_file, 'r') as x:
            settings = json.load(x)
        for i in settings["mod roles"][0]:
            print(i)

        for role in ctx.author.roles:
            if role.name == role_name:
                return True
        return False
    return commands.check(predicate)

### loop to check if user is streaming ###

async def start_bot():
    c = 1
    while True:
        await check_twitch() # checks if user is streaming
        await asyncio.sleep(5) # waits 5 seconds
        if tse == True: # if tse is true it will continue checking else stop checking
            print(f"check {c}")
            c = c + 1

### checks if user is streaming ###

async def check_twitch():
    global tse
    if tse == True:
        notified = False
        try:
            user_data_gen = twitch.get_users(logins=[twitch_username]) # creates a async generator to get the stream(s)
            user_info = await anext(user_data_gen, None) # gets the first user from the generator
            if user_info is None: # checks if the user exists
                print("User not found")
                return

            user_id = user_info.id # getting the id of the user

            stream_data_gen = twitch.get_streams(user_id=[user_id]) # gets streamer details
            stream_info = await anext(stream_data_gen, None) # checks if there streaming and gets stream details
            
            channel = bot.get_channel(live_channel_id) # gets live channel
            
            if stream_info and not notified: # checks if the streamer is streaming and if its notified yet
                print(f"{twitch_username} is live and embed is sent")
                embed = discord.Embed(title=f"{twitch_username} is now live on Twitch!", description=f"**{stream_info.title}**", color=discord.Color.purple())
                embed.add_field(name="Game", value=stream_info.game_name or "Unknown", inline=True)
                embed.add_field(name="Viewers", value=stream_info.viewer_count or 0, inline=True)
                embed.set_image(url=stream_info.thumbnail_url.format(width=320, height=180))
                embed.set_footer(text="bot created by: ジョシュア")

                view = discord.ui.View()
                url_button = discord.ui.Button(label="Watch Stream", url=f"https://twitch.tv/{twitch_username}")
                view.add_item(url_button)

                await channel.send(content=f"come check out {twitch_username}'s stream <@1385828781738033202>", embed=embed, view=view)
                notified = True
            elif not stream_info:
                notified = False

        except Exception as e: # catches twitch API errors
            print(f"Twitch API error: {e}")

### on start of bot ###

@bot.event
async def on_ready():
    if not os.path.exists(settings_file): # checks if the settings file exists
        with open(settings_file,"w") as x: # makes settings file
            settings = {
                            "wellcome/goodbye settings":
                            {
                                "wellcome settings":[
                                    {"wellcome_enabled": False,
                                    "wellcome_channel": None}
                                ],
                                "goodbye settings": [
                                    {"goodbye_enabled": False,
                                    "goodbye_channel": None}
                                ]
                            },
                            "mod roles":
                            {
                                {
                                    "owner role":None,
                                    "admin role":None,
                                    "mod role":None
                                }
                            }
                        }
            json.dump(settings, x, indent=2) # writes to settings file
    await twitch.authenticate_app([])
    asyncio.create_task(start_bot())
    print(f"bot ready")

### on message ###
    
@bot.event
async def on_message(message):
    if message.author == bot.user: # returns if message is from bot
        return
    
    print(message.content)

    now = datetime.datetime.now() # gets current time
    formatted = now.strftime("%Y-%m-%d %I:%M:%S %p") # formats time
    
    log = { # message log
        "author": message.author.display_name,
        "user_id": message.author.id,
        "message": message.content,
        "time-send": formatted
    }
    
    with open(logs_file,"a") as logs: # writes message log to json file
        logs.write(json.dumps(log, ensure_ascii=False, indent=2) + "\n")

### on member join ###

@bot.event
async def on_member_join(member):
    with open(settings_file,'r') as x:
        settings = json.load(x)

    if settings["wellcome/goodbye settings"]["wellcome settings"][0]["wellcome_enabled"] == True:
        channel = bot.get_channel(settings["wellcome/goodbye settings"]["wellcome settings"][0]["wellcome_channel"])
        embed_wellcome = discord.Embed(description=f"wellcome to {member.guild.name}",color=0x22b111)
        embed_wellcome.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed_wellcome.add_field(name="", value=f"Bot created by: <@303737328437035008>", inline=False)
        embed_wellcome.add_field(name="", value=f"Server created by: {member.guild.owner.mention}", inline=False)
        embed_wellcome.set_image(url="https://i.imgur.com/2fRNx2E.jpeg")
        embed_wellcome.set_footer(text=f"There are now {member.guild.member_count} members!")
        await channel.send(member.mention, embed=embed_wellcome)

### tests join embed ###

@bot.slash_command(name="test-join")
@commands.is_owner()
async def test_join(ctx):
    with open(settings_file,'r') as x:
        settings = json.load(x)

    if settings["wellcome/goodbye settings"]["wellcome settings"][0]["wellcome_enabled"] == True:
        embed_wellcome = discord.Embed(description=f"wellcome to {ctx.author.guild.name}",color=0x22b111)
        embed_wellcome.set_author(name=ctx.author)
        embed_wellcome.add_field(name="", value=f"Bot created by: <@303737328437035008>", inline=False)
        embed_wellcome.add_field(name="", value=f"Server created by: {ctx.guild.owner.mention}", inline=False)
        embed_wellcome.set_image(url="https://i.imgur.com/2fRNx2E.jpeg")
        embed_wellcome.set_footer(text=f"There are now {ctx.guild.member_count} members!")
        await ctx.respond(ctx.author.mention, embed=embed_wellcome)
    else:
        await ctx.respond("join not enabled", ephemeral=True)

### sets the join channel and bool var ###

@bot.slash_command(name="set_join_embed")
@commands.is_owner()
async def join_channel(ctx, channel:discord.Option(discord.TextChannel, 'channel for join embed'), enable:bool): # type: ignore # <<< removes useless error message
    with open(settings_file,"r") as x:
        settings = json.load(x)

    settings["wellcome/goodbye settings"]["wellcome settings"][0]["wellcome_enabled"] = enable
    settings["wellcome/goodbye settings"]["wellcome settings"][0]["wellcome_channel"] = channel.id
    await ctx.respond(f"wellcome = {str(enable)}\nwellcome channel = {str(channel)}", ephemeral=True)
    
    with open(settings_file,'w') as x:
        json.dump(settings, x, indent=2)

### on member remove ###

@bot.event
async def on_member_remove(member):
    with open(settings_file,'r') as x:
        settings = json.load(x)

    if settings["wellcome/goodbye settings"]["goodbye settings"][0]["goodbye_enabled"] == True:
        channel = bot.get_channel(settings["wellcome/goodbye settings"]["goodbye settings"][0]["goodbye_channel"])
        embed_leave = discord.Embed(title=f"{member}", description=f"{member} has left the server",color=0x22b111)
        embed_leave.set_image(url="https://i.imgur.com/2fRNx2E.jpeg")
        await channel.send(embed=embed_leave)

### tests leave embed ###

@bot.slash_command(name="test-leave")
@commands.is_owner()
async def test_leave(ctx):
    with open(settings_file,'r') as x:
        settings = json.load(x)
    
    if settings["wellcome/goodbye settings"]["goodbye settings"][0]["goodbye_enabled"] == True:
        embed_leave = discord.Embed(title=f"{ctx.author}", description=f"{ctx.author} has left the server",color=0x22b111)
        embed_leave.set_image(url="https://i.imgur.com/2fRNx2E.jpeg")
        await ctx.respond(embed=embed_leave)

### sets leave embed channel and bool var ###

@bot.slash_command(name="set_leave_embed", description="put \"None\" to not change it")
@commands.is_owner()
async def leave_channel(ctx, channel:discord.Option(discord.TextChannel, 'channel for leave embed'), enable:bool): # type: ignore # <<< removes useless error message
    with open(settings_file,"r") as x:
        settings = json.load(x)

    settings["wellcome/goodbye settings"]["goodbye settings"][0]["goodbye_enabled"] = enable
    settings["wellcome/goodbye settings"]["goodbye settings"][0]["goodbye_channel"] = channel.id
    await ctx.respond(f"goodbye = {str(enable)}\ngoodbye channel = {str(channel)}")

    with open(settings_file,'w') as x:
        json.dump(settings, x, indent=2)

### tests twitch notify embed ###

@bot.slash_command(name="testnotify", description="Send a test Twitch notification.", ephemeral=True)
@commands.is_owner()
async def testnotify(ctx):
    embed = discord.Embed(title=f"(streamer name here) is now live on Twitch!", description=f"(title here)", color=discord.Color.purple())
    embed.add_field(name="Game", value="(game here)", inline=True)
    embed.add_field(name="Viewers", value="(viewer count here)", inline=True)
    embed.set_image(url="https://projects.thepostathens.com/SpecialProjects/ohio-university-faculty-student-diversity/img/placeholder.jpg")
    embed.set_footer(text="bot created by: ジョシュア")

    view = discord.ui.View()
    url_button = discord.ui.Button(label="Watch Stream", url="https://tinyurl.com/yz66web9")
    view.add_item(url_button)

    await ctx.respond(content=f"come check out (username here)'s stream (ping role goes here)", embed=embed, view=view)

### on message delete

@bot.event
async def on_message_delete(message):
    if message.author == bot.user:
        return

    logs = bot.get_channel(1406876339243450409)
    delem = discord.Embed(title="message deleted", description="message content:", color=discord.Color.purple())
    delem.add_field(name="", value="", inline=True)
    delem.add_field(name="", value=message.content, inline=True)
    delem.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
    await logs.send(embed=delem)

### when someone join/leaves a vc ###

@bot.event
async def on_voice_state_update(member, before, after):
    logs = bot.get_channel(1406876339243450409)
    if before.channel is None and after.channel is not None:
        print(f"{member} joined {after.channel}")

        joinem = discord.Embed(title="member joined channel", description=f"joined {after.channel}", color=discord.Color.purple())
        joinem.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        await logs.send(embed=joinem)

    elif before.channel is not None and after.channel is None:
        print(f"{member} left {before.channel}")

        leaveem = discord.Embed(title="member left channel", description=f"left {before.channel}", color=discord.Color.purple())
        leaveem.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        await logs.send(embed=leaveem)

### test roles req ###

@bot.slash_command(name="test-roles-req")
@role_required("Owner")
async def test_role(ctx):
    ctx.respond("you have Owner role")

### runs bot ###

bot.run(bot_token)