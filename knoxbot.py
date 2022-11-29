# ENV related imports
from dotenv import load_dotenv
from os import getenv as ENV
# Path related imports
from os.path import join, dirname
# Discord related imports
import discord
from discord.ext import commands
# Importing my utility files
import utils.pnw_utils as pnw
from utils.utils import *

# Load the env from its path
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
# Get important, constant info from the env
TOKEN = ENV("DISCORD_TOKEN")
GUILD = ENV('DISCORD_GUILD')
LOG = open(ENV('LOG_DIRECTORY'), "a")
admins, allowed_guilds = start(dotenv_path)

#Initialize the bot with a set prefix of ! and all possible Intents
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())





##############
#            #
# BOT EVENTS #
#            #
##############





# Event for when the bot is ready
@bot.event
async def on_ready():
    # Call the start function to intialize the global admin and allowed_guilds variables
    start(dotenv_path)
    # Some random bs from the starter code that I will likely delete at some point
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name} (id: {guild.id})'
    )
    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')

# Event for when a command error occurs
@bot.event
async def on_command_error(ctx, error):
    # If the error is that the attempted command does not exist
    if isinstance(error, commands.CommandNotFound):
        # Send a silly little message saying it doesn't exist (will change to an embed later)
        await ctx.send("Oops... that command doesn't exist.")
        # Log that the user attempted to use this fictional command
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use command: {ctx.message.content}\n')
        LOG.flush()
        # Return, so the error is not raised and bothers me in the console
        return
    raise error





#############################
#                           #
# POLITICS AND WAR COMMANDS #
#                           #
#############################





########################
# CALCULATION COMMANDS #
########################


# Add a command to calculate the cost of infrastructure
@bot.command(name='pnwinfra')
async def calc_infra(ctx, *args):
    # If the message was not sent in a permitted guild
    if not check_guild(ctx.guild, allowed_guilds):
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use the !pnwinfra command in guild {ctx.guild.id}.\n')
        LOG.flush()
        await ctx.send("You do not have permission to use commands in this server. Please contact an admin for support.")
        return
    # If there are less than two arguments or more than three arguments, then it isn't a valid command call
    if len(args) < 2 or len(args) > 3:
        embed=discord.Embed(title="Invalid Arguments", description="This function requires two or three arguments:\n!pnwinfra [nation id] [start] [end]\n!pnwinfra [start] [end]", color=0xFF5733)
    # If there are two arguments, then just calculate the difference between the two
    elif len(args) == 2:
        infra_cost = pnw.calculate_infrastructure_value(float(args[0]), float(args[1]))
        embed=discord.Embed(title="Calculate Infrastructure Cost", description=f'The cost to go from {args[0]} to {args[1]} is:\n${infra_cost: ,.2f}', color=0xFF5733)
    # If there are three arguments, then calculate the difference between the two considering their nation
    elif len(args) == 3:
        # Get the infra query result
        result = pnw.get_query("infra", args[0])
        infra_cost = pnw.calc_infra_cost(result, float(args[1]), float(args[2]))
        embed=discord.Embed(title="Calculate Infrastructure Cost", description=f'The cost to go from {args[1]: ,.2f} to {args[2]: ,.2f} for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={args[0]}) is:\n${infra_cost: ,.2f}', color=0xFF5733)
    # Log the command usage
    LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwinfra command with args: {args}.\n')
    LOG.flush()
    await ctx.send(embed=embed)

# Add a command to calculate the cost to go from a city to another city
@bot.command(name='pnwcity')
async def calc_city(ctx, start, end, nation_id = None):
    if not check_guild(ctx.guild, allowed_guilds):
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use the !pnwcity command in guild {ctx.guild.id}.\n')
        LOG.flush()
        await ctx.send("You do not have permission to use commands in this server. Please contact an admin for support.")
        return
    if nation_id is not None:
        # Get the city query result
        result = pnw.get_query("city", nation_id)
        city_cost = pnw.calc_city_cost(int(start), int(end), result)
        embed=discord.Embed(title="Calculate City Cost", description=f'The cost to go from {start} to {end} for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}) is:\n${city_cost: ,.2f}', color=0xFF5733)
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !city command with id {nation_id}, start {start}, and end {end}.\n')
    else:
        city_cost = pnw.calc_city_cost(int(start), int(end))
        embed=discord.Embed(title="Calculate City Cost", description=f'The cost to go from {start} to {end} is:\n${city_cost: ,.2f}', color=0xFF5733)
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwcity command with start {start} and end {end}.\n')
    # Log the command usage
    LOG.flush()
    await ctx.send(embed=embed)


####################
# REVENUE COMMANDS #
####################


# Add a command to calculate food revenue (usage, production, and net revenue) of a nation
@bot.command(name="pnwfood")
async def calc_food(ctx, nation_id):
    if not check_guild(ctx.guild, allowed_guilds):
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use the !pnwfood command in guild {ctx.guild.id}.\n')
        LOG.flush()
        await ctx.send("You do not have permission to use commands in this server. Please contact an admin for support.")
        return
    # Get the food query result
    result = pnw.get_query("food", nation_id)
    net_food, food_production, food_usage = pnw.calc_food_rev(result)
    embed=discord.Embed(title="Food Statistics", description=f'Statistics about food revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {abs(food_production): ,.2f}\nUsage: {food_usage: ,.2f}\nNet: {net_food: ,.2f}', color=0xFF5733)
    # Log the command usage
    LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwfood command with id {nation_id}.\n')
    LOG.flush()
    await ctx.send(embed=embed)

@bot.command(name="pnwcoal")
async def calc_coal(ctx, nation_id):
    if not check_guild(ctx.guild, allowed_guilds):
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use the !pnwcoal command in guild {ctx.guild.id}.\n')
        LOG.flush()
        await ctx.send("You do not have permission to use commands in this server. Please contact an admin for support.")
        return
    # Get the coal query result
    result = pnw.get_query("coal", nation_id)
    net_coal, coal_production, coal_usage = pnw.calc_coal_rev(result)
    embed=discord.Embed(title="Coal Statistics", description=f'Statistics about coal revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {abs(coal_production): ,.2f}\nUsage: {coal_usage: ,.2f}\nNet: {net_coal: ,.2f}', color=0xFF5733)
    # Log the command usage
    LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwcoal command with id {nation_id}.\n')
    LOG.flush()
    await ctx.send(embed=embed)


#################
# USER COMMANDS #
#################


@bot.command(name="mypnwinfo")
async def my_info(ctx, nation_id, api_key=None):
    await ctx.message.delete()
    # If they specified an API key, then they want to display sensitive information
    if api_key is not None:
        result = pnw.get_query("my_info", nation_id, api_key)
        nation = result.nations[0]
        embed=discord.Embed(title=f'Info for {nation.nation_name}',description=f'Military\nSoldiers: {nation.soldiers}\nTanks: {nation.tanks}\nAircraft: {nation.aircraft}\nShips: {nation.ships}')
    # Otherwise, they only want to display non-sensitive information
    else:
        result = pnw.get_query("my_info", nation_id)
        nation = result.nations[0]
        embed=discord.Embed(title=f'Info for {nation.nation_name}',description=f'Military\nSoldiers: {nation.soldiers}\nTanks: {nation.tanks}\nAircraft: {nation.aircraft}\nShips: {nation.ships}')
    # Log the command usage
    LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !mypnwinfo command with id {nation_id}.\n')
    LOG.flush()
    await ctx.send(embed=embed)





##################
#                #
# ADMIN COMMANDS #
#                #
##################





# Add a command to clear the commands log
@bot.command(name="clearlog")
async def clear_log(ctx):
    # If the command user is an admin, then clear the log
    if ctx.message.author.id in admins:
        with open("commands_log.log",'w') as _:
            pass
        embed=discord.Embed(title="Log Clear", description=f'Admin {ctx.message.author} ({ctx.message.author.id}) has cleared the logs.', color=0xFF5733)
    # Otherwise, send an improper access message
    else:
        embed=discord.Embed(title="Improper Access", description=f'User {ctx.message.author} ({ctx.message.author.id}) does not have permissions to run this command. Contact an Admin to resolve this issue.', color=0xFF5733)
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to clear the logs, but did not have proper access.\n')
        LOG.flush()
    await ctx.send(embed=embed)

# Add a command to shut the bot off
@bot.command(name="shutoff")
async def shutoff(ctx):
    # If the command user is an admin, then shut the bot off
    if ctx.message.author.id in admins:
        # Create an embed saying that the bot was shut off by this specific admin
        embed=discord.Embed(title="Bot Shutoff", description=f'Admin {ctx.message.author} ({ctx.message.author.id}) has shutoff the bot.', color=0xFF5733)
        # Write to the log that the bot was shut off
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) shut the bot off.\n')
        LOG.flush()
        # Send the embed and shut the bot off
        await ctx.send(embed=embed)
        await bot.close()
    # Otherwise, send an improper access message and log that they attempted it
    else:
        embed=discord.Embed(title="Improper Access", description=f'User {ctx.message.author} ({ctx.message.author.id}) does not have permissions to run this command. Contact an Admin to resolve this issue.', color=0xFF5733)
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to shut off the bot, but did not have proper access.\n')
        LOG.flush()
        await ctx.send(embed=embed)

@bot.command(name="addserver")
async def add_server(ctx, guild_id=None):
    global admins, allowed_guilds
    if guild_id is None:
        guild_id = ctx.guild.id
    if ctx.message.author.id in admins:
        if check_guild(ctx.guild, allowed_guilds):
            embed=discord.Embed(title="Already Permitted", description=f'Server {guild_id} is already an allowed server for bot commands.')
            LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to add server {guild_id}, but that server already has permission.\n')
            LOG.flush()
            await ctx.send(embed=embed)
            return
        found = False
        with open(dotenv_path, "r") as f:
            lines = f.readlines()
        with open(dotenv_path, "w") as f:
            for line in lines:
                try:
                    key, value = line.split('=')
                    if key == "ALLOWED_GUILDS":
                        value = f'{value},{guild_id}'
                        found = True
                    f.write(f'{key}={value}')
                except ValueError:
                    # syntax error
                    pass
            if not found:
                f.write(f'\nALLOWED_GUILDS={guild_id}')
        admins, allowed_guilds = start(dotenv_path)
    else:
        embed=discord.Embed(title="Improper Access", description=f'User {ctx.message.author} ({ctx.message.author.id}) does not have permissions to run this command. Contact an Admin to resolve this issue.', color=0xFF5733)
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to add server {guild_id}, but did not have proper access.\n')
        LOG.flush()
        await ctx.send(embed=embed)
        return

bot.run(TOKEN)