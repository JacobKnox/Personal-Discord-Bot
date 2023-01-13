import os
import sys
import typing
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
ERROR_LOG = open(ENV('ERROR_LOG_DIRECTORY'), "a")
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
        # Send a message saying it doesn't exist
        embed = discord.Embed(title="Command Not Found", description=f"The command you attempted to use, {ctx.message.content}, does not currently exist.", color=0xFF5733)
        await ctx.send(embed=embed)
        # Log that the user attempted to use this fictional command
        ERROR_LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use non-existent command: {ctx.message.content}\n')
        ERROR_LOG.flush()
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
async def calc_infra(ctx, start: typing.Optional[float], end: typing.Optional[float], nation_id: typing.Optional[int] = None, *, args = None):
    embed, flag = generic_tasks(LOG, ctx, allowed_guilds, args = [start, end, nation_id, args])
    if flag:
        await ctx.send(embed=embed)
        return
    # If there are two arguments, then just calculate the difference between the two
    elif nation_id is None:
        infra_cost = pnw.calculate_infrastructure_value(start, end)
        embed=discord.Embed(title="Calculate Infrastructure Cost", description=f'The cost to go from {start} to {end} is:\n${infra_cost: ,.2f}', color=0xFF5733)
    # If there are three arguments, then calculate the difference between the two considering their nation
    elif nation_id is not None:
        # Get the infra query result
        result = pnw.get_query("infra", nation_id)
        infra_cost = pnw.calc_infra_cost(start, end, result)
        embed=discord.Embed(title="Calculate Infrastructure Cost", description=f'The cost to go from {start} to {end} for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}) is:\n${infra_cost: ,.2f}', color=0xFF5733)
    # Log the command usage
    LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwinfra command.\n')
    LOG.flush()
    await ctx.send(embed=embed)

# Add a command to calculate the cost to go from a city to another city
@bot.command(name='pnwcity')
async def calc_city(ctx, start: typing.Optional[int], end: typing.Optional[int], nation_id: typing.Optional[int] = None, *, args = None):
    embed, flag = generic_tasks(LOG, ctx, allowed_guilds, args = [start, end, nation_id, args])
    if flag:
        await ctx.send(embed=embed)
        return
    elif nation_id is None:
        city_cost = pnw.calc_city_cost(start, end)
        embed=discord.Embed(title="Calculate City Cost", description=f'The cost to go from {start} to {end} is:\n${city_cost: ,.2f}', color=0xFF5733)
    elif nation_id is not None:
        # Get the city query result
        result = pnw.get_query("city", nation_id)
        city_cost = pnw.calc_city_cost(start, end, result)
        embed=discord.Embed(title="Calculate City Cost", description=f'The cost to go from {start} to {end} for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}) is:\n${city_cost: ,.2f}', color=0xFF5733)
    # Log the command usage
    LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwcity command.\n')
    LOG.flush()
    await ctx.send(embed=embed)


####################
# REVENUE COMMANDS #
####################


# Add a command to calculate food revenue (usage, production, and net revenue) of a nation
@bot.command(name="pnwfood")
async def calc_food(ctx, nation_id: typing.Optional[int], *, args=None):
    embed, flag = generic_tasks(LOG, ctx, allowed_guilds, args = [nation_id, args])
    if flag:
        await ctx.send(embed=embed)
        return
    # Get the food query result
    result = pnw.get_query("food", nation_id)
    net_food, food_production, food_usage = pnw.calc_food_rev(result)
    embed=discord.Embed(title="Food Statistics", description=f'Statistics about food revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {abs(food_production): ,.2f}\nUsage: {food_usage: ,.2f}\nNet: {net_food: ,.2f}', color=0xFF5733)
    # Log the command usage
    LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwfood command with id {nation_id}.\n')
    LOG.flush()
    await ctx.send(embed=embed)

# Add a command to calculate coal revenue (usage, production, and net revenue) of a nation
@bot.command(name="pnwcoal")
async def calc_coal(ctx, nation_id: typing.Optional[int], *, args=None):
    embed, flag = generic_tasks(LOG, ctx, allowed_guilds, args = [nation_id, args])
    if flag:
        await ctx.send(embed=embed)
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
async def my_info(ctx, nation_id: typing.Optional[int], api_key: typing.Optional[str]=None, *, args=None):
    await ctx.message.delete()
    embed, flag = generic_tasks(LOG, ctx, allowed_guilds, args = [nation_id, api_key, args])
    if flag:
        await ctx.send(embed=embed)
        return
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
        await ctx.send(embed=embed)
        return
    # Handle if they're not an admin
    await non_admin(LOG, ctx)

# Add a command to shut the bot off
@bot.command(name="shutoff")
async def shutoff(ctx):
    # Check if the user attempting to use the command is an admin
    if not ctx.message.author.id in admins:
        # Handle if they're not an admin
        await non_admin(LOG, ctx)
        return
    # Create an embed saying that the bot was shut off by this specific admin
    embed=discord.Embed(title="Bot Shutoff", description=f'Admin {ctx.message.author} ({ctx.message.author.id}) has shutoff the bot.', color=0xFF5733)
    # Write to the log that the bot was shut off
    LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) shut the bot off.\n')
    LOG.flush()
    # Send the embed and shut the bot off
    await ctx.send(embed=embed)
    await bot.close()

# Add a command to restart the bot
@bot.command(name="restart")
async def restart(ctx):
    # Check if the user attempting to use the command is an admin
    if not ctx.message.author.id in admins:
        # Handle if they're not an admin
        await non_admin(LOG, ctx)
        return
    # Create an embed saying that the bot was restart by this specific admin
    embed=discord.Embed(title="Bot Restart", description=f'Admin {ctx.message.author} ({ctx.message.author.id}) has restarted the bot.', color=0xFF5733)
    # Write to the log that the bot was restart
    LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) restarted the bot.\n')
    LOG.flush()
    # Send the embed
    await ctx.send(embed=embed)
    # Re-execute this file to restart the bot
    os.execv(sys.executable, ['python'] + sys.argv)
    

# Add a command to add a server to the permitted list of servers
@bot.command(name="addserver")
async def add_server(ctx, guild_id=None):
    global admins, allowed_guilds
    # Check if the user attempting to run the command is an admin
    if not ctx.message.author.id in admins:
        # Handle if they're not an admin
        await non_admin(LOG, ctx)
        return
    # If the user does not specify a guild_id, then they want to add the server they used the command in
    if guild_id is None:
        guild_id = ctx.guild.id
    # Check if the guild is already a permitted guild
    if check_guild(ctx.guild, allowed_guilds):
        # Log and message telling that it is
        embed=discord.Embed(title="Already Permitted", description=f'Server {guild_id} is already an allowed server for bot commands.')
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to add server {guild_id}, but that server already has permission.\n')
        LOG.flush()
        await ctx.send(embed=embed)
        return
    # Create a flag to indicate whether or not the ALLOWED_GUILDS variable is found in the .env
    found = False
    # Open the .env and read all the lines
    with open(dotenv_path, "r") as f:
        lines = f.readlines()
    # Open the .env again in write mode
    with open(dotenv_path, "w") as f:
        # Loop through the lines read in
        for line in lines:
            try:
                # Split the key and values on =
                key, value = line.split('=')
                # Check if the key is ALLOWED_GUILDS
                if key == "ALLOWED_GUILDS":
                    # If it is, then append the guild_id to the current value
                    value = f'{value},{guild_id}'
                    # Mark the found flag true
                    found = True
                # Write the key and value to the .env again
                f.write(f'{key}={value}')
            except ValueError:
                # syntax error
                pass
        # If the key is not found, then there are no allowed guilds yet, so I need to add it to the .env
        if not found:
            f.write(f'\nALLOWED_GUILDS={guild_id}')
    # Re-assign the admins and allowed_guilds variables to account for the changes to the .env
    admins, allowed_guilds = start(dotenv_path)
    # Create an embed saying that the server was added successfully and send it
    embed=discord.Embed(title="Server Added", description=f"Admin {ctx.message.author} ({ctx.message.author.id}) has added the guild {guild_id} to the bot's permitted guilds.", color=0xFF5733)
    await ctx.send(embed=embed)

bot.run(TOKEN)