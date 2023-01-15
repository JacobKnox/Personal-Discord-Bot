import time
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
start_time = 0

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
    print(f'{bot.user} is connected to the following guilds:')
    for guild in bot.guilds:
        print(f'\n{guild.name} (id: {guild.id})')
    await bot.add_cog(PoliticsandWar(bot))
    await bot.add_cog(Moderation(bot))
    await bot.add_cog(BotAdmin(bot))
    print("Bot is ready to use!")

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
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        # Send a message saying the user missed required arguments
        cmd = bot.get_command(str(ctx.command))
        embed = discord.Embed(title="Missing Arguments", description=f"Command usage:\n{cmd.usage}", color=0xFF5733)
        await ctx.send(embed=embed)
        # Log that the user attempted to use this fictional command
        ERROR_LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) improperly used command: {ctx.command}\n')
        ERROR_LOG.flush()
        return
    me = bot.get_user(admins[0])
    await me.send(f"There has been an error: {error.__class__.__name__}\n{', '.join(error.args)}\nRaised when attempted: {ctx.message.content}")
    return





#############################
#                           #
# POLITICS AND WAR COMMANDS #
#                           #
#############################
class PoliticsandWar(commands.Cog, name="Politics and War", description="All commands related to the Politics and War browser game."):
    ########################
    # CALCULATION COMMANDS #
    ########################


    # Add a command to calculate the cost of infrastructure
    @commands.command(name='pnwinfra', help="Calculates the cost to go from one level of infrastructure to another, optionally for a specific nation.", brief="Calculates cost of infrastrucutre.", usage="!pnwinfra start end (nation_id)")
    async def calc_infra(self, ctx, start: float = commands.parameter(description="Starting infrastructure level"), end: float = commands.parameter(description="Ending instrastructure level"), nation_id: typing.Optional[int] = commands.parameter(default=None, description="ID of the nation to calculate for")):
        # If there are two arguments, then just calculate the difference between the two
        if nation_id is None:
            infra_cost = pnw.calculate_infrastructure_value(start, end)
            embed=discord.Embed(title="Calculate Infrastructure Cost", description=f'The cost to go from {start} to {end} is:\n${infra_cost: ,.2f}', color=0xFF5733)
        # If there are three arguments, then calculate the difference between the two considering their nation
        else:
            # Get the infra query result
            result = pnw.get_query("infra", nation_id)
            infra_cost = pnw.calc_infra_cost(start, end, result)
            embed=discord.Embed(title="Calculate Infrastructure Cost", description=f'The cost to go from {start} to {end} for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}) is:\n${infra_cost: ,.2f}', color=0xFF5733)
        # Log the command usage
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwinfra command.\n')
        LOG.flush()
        await ctx.send(embed=embed)

    # Add a command to calculate the cost to go from a city to another city
    @commands.command(name='pnwcity', help="Calculates the cost to go from one city to another, optionally for a specific nation.", brief="Calculates the cost of cities.", usage="!pnwcity start end (nation_id)")
    async def calc_city(self, ctx, start: int = commands.parameter(description="Starting city level"), end: int = commands.parameter(description="Ending city level"), nation_id: typing.Optional[int] = commands.parameter(default=None, description="ID of the nation to calculate for")):
        if nation_id is None:
            city_cost = pnw.calc_city_cost(start, end)
            embed=discord.Embed(title="Calculate City Cost", description=f'The cost to go from {start} to {end} is:\n${city_cost: ,.2f}', color=0xFF5733)
        else:
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
    @commands.command(name="pnwfood", help="Calculates the food usage, production, and net revenue for a nation.", brief="Calculates food stats for a nation.", usage="!pnwfood nation_id")
    async def calc_food(self, ctx, nation_id: int = commands.parameter(description="ID of the nation to calculate for")):
        # Get the food query result
        result = pnw.get_query("food", nation_id)
        net_food, food_production, food_usage = pnw.calc_food_rev(result)
        embed=discord.Embed(title="Food Statistics", description=f'Statistics about food revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {abs(food_production): ,.2f}\nUsage: {food_usage: ,.2f}\nNet: {net_food: ,.2f}', color=0xFF5733)
        # Log the command usage
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwfood command with id {nation_id}.\n')
        LOG.flush()
        await ctx.send(embed=embed)

    # Add a command to calculate coal revenue (usage, production, and net revenue) of a nation
    @commands.command(name="pnwcoal", help="Calculates the coal usage, production, and net revenue for a nation.", brief="Calculates coal stats for a nation.", usage="!pnwcoal nation_id")
    async def calc_coal(self, ctx, nation_id: int = commands.parameter(description="ID of the nation to calculate for")):
        result, flag = resource_tasks(nation_id)
        if flag:
            await ctx.send(embed=result)
            return
        net_coal, coal_production, coal_usage = pnw.calc_coal_rev(result)
        embed=discord.Embed(title="Coal Statistics", description=f'Statistics about coal revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {abs(coal_production): ,.2f}\nUsage: {coal_usage: ,.2f}\nNet: {net_coal: ,.2f}', color=0xFF5733)
        # Log the command usage
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwcoal command with id {nation_id}.\n')
        LOG.flush()
        await ctx.send(embed=embed)
    
    # Add a command to calculate lead revenue (usage, production, and net revenue) of a nation
    @commands.command(name="pnwlead", help="Calculates the lead usage, production, and net revenue for a nation.", brief="Calculates lead stats for a nation.", usage="!pnwlead nation_id")
    async def calc_lead(self, ctx, nation_id: int = commands.parameter(description="ID of the nation to calculate for")):
        result, flag = resource_tasks(nation_id)
        if flag:
            await ctx.send(embed=result)
            return
        net_lead, lead_production, lead_usage = pnw.calc_lead_rev(result)
        embed=discord.Embed(title="Lead Statistics", description=f'Statistics about lead revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {abs(lead_production): ,.2f}\nUsage: {lead_usage: ,.2f}\nNet: {net_lead: ,.2f}', color=0xFF5733)
        # Log the command usage
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwlead command with id {nation_id}.\n')
        LOG.flush()
        await ctx.send(embed=embed)
        
    # Add a command to calculate bauxite revenue (usage, production, and net revenue) of a nation
    @commands.command(name="pnwbauxite", help="Calculates the bauxite usage, production, and net revenue for a nation.", brief="Calculates bauxite stats for a nation.", usage="!pnwbauxite nation_id")
    async def calc_bauxite(self, ctx, nation_id: int = commands.parameter(description="ID of the nation to calculate for")):
        result, flag = resource_tasks(nation_id)
        if flag:
            await ctx.send(embed=result)
            return
        net_bauxite, bauxite_production, bauxite_usage = pnw.calc_bauxite_rev(result)
        embed=discord.Embed(title="Bauxite Statistics", description=f'Statistics about bauxite revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {abs(bauxite_production): ,.2f}\nUsage: {bauxite_usage: ,.2f}\nNet: {net_bauxite: ,.2f}', color=0xFF5733)
        # Log the command usage
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwbauxite command with id {nation_id}.\n')
        LOG.flush()
        await ctx.send(embed=embed)
        
    # Add a command to calculate oil revenue (usage, production, and net revenue) of a nation
    @commands.command(name="pnwoil", help="Calculates the oil usage, production, and net revenue for a nation.", brief="Calculates oil stats for a nation.", usage="!pnwoil nation_id")
    async def calc_oil(self, ctx, nation_id: int = commands.parameter(description="ID of the nation to calculate for")):
        result, flag = resource_tasks(nation_id)
        if flag:
            await ctx.send(embed=result)
            return
        net_oil, oil_production, oil_usage = pnw.calc_oil_rev(result)
        embed=discord.Embed(title="Oil Statistics", description=f'Statistics about oil revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {abs(oil_production): ,.2f}\nUsage: {oil_usage: ,.2f}\nNet: {net_oil: ,.2f}', color=0xFF5733)
        # Log the command usage
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwoil command with id {nation_id}.\n')
        LOG.flush()
        await ctx.send(embed=embed)
        
    # Add a command to calculate iron revenue (usage, production, and net revenue) of a nation
    @commands.command(name="pnwiron", help="Calculates the iron usage, production, and net revenue for a nation.", brief="Calculates iron stats for a nation.", usage="!pnwiron nation_id")
    async def calc_iron(self, ctx, nation_id: int = commands.parameter(description="ID of the nation to calculate for")):
        result, flag = resource_tasks(nation_id)
        if flag:
            await ctx.send(embed=result)
            return
        net_iron, iron_production, iron_usage = pnw.calc_iron_rev(result)
        embed=discord.Embed(title="Iron Statistics", description=f'Statistics about iron revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {abs(iron_production): ,.2f}\nUsage: {iron_usage: ,.2f}\nNet: {net_iron: ,.2f}', color=0xFF5733)
        # Log the command usage
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwiron command with id {nation_id}.\n')
        LOG.flush()
        await ctx.send(embed=embed)


    #################
    # USER COMMANDS #
    #################


    @commands.command(name="mypnwinfo", enabled=False)
    async def my_info(self, ctx, nation_id: int = commands.parameter(description="ID of the nation whose information is to be displayed"), api_key: typing.Optional[str]=commands.parameter(default=None, description="User's API key, used to access their personal information for display")):
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
    
    async def cog_check(self, ctx):
        return await generic_tasks(LOG, ctx, allowed_guilds)




################
#              #
# MOD COMMANDS #
#              #
################
class Moderation(commands.Cog, description="Moderation commands"):
    @commands.command(name="ban", enabled=False, help="Ban one or more user(s) with a specified reason", brief="Ban people", usage="!ban @Jacob @Wumpus Bad people")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, members: commands.Greedy[discord.Member] = commands.parameter(description="User(s) to ban"), *, reason: typing.Optional[str] = commands.parameter(default=None, description="Reason for banning the user(s)")):
        for member in members:
            await member.ban(reason = reason)
        embed = discord.Embed(title="Wall of Bans", description=f"The following Discord users have joined the Wall of Bans of {ctx.guild.name} for the reason '{reason}':\n{', '.join(f'{member.name} ({member.id})' for member in members)}")
        await ctx.send(embed=embed)
    
    async def cog_check(self, ctx):
        return await generic_tasks(LOG, ctx, allowed_guilds)





######################
#                    #
# BOT ADMIN COMMANDS #
#                    #
######################
class BotAdmin(commands.Cog, name="Bot Admin", description="Commands for admins of the bot"):
    # Add a command to clear the commands log
    @commands.command(name="clearlog", help="Clears all of the logs associated with the bot", brief="Clears logs", usage="!clearlogs")
    async def clear_log(self, ctx):
        with open(ENV('LOG_DIRECTORY'),'w') as _:
            pass
        with open(ENV('ERROR_LOG_DIRECTORY'),'w') as _:
            pass
        embed=discord.Embed(title="Log Clear", description=f'Admin {ctx.message.author} ({ctx.message.author.id}) has cleared the logs.', color=0xFF5733)
        await ctx.send(embed=embed)

    # Add a command to shut the bot off
    @commands.command(name="shutoff", help="Shuts the bot off completly", brief="Shut bot off", usage="!shutoff")
    async def shutoff(self, ctx):
        # Create an embed saying that the bot was shut off by this specific admin
        embed=discord.Embed(title="Bot Shutoff", description=f'Admin {ctx.message.author} ({ctx.message.author.id}) has shutoff the bot.', color=0xFF5733)
        # Write to the log that the bot was shut off
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) shut the bot off.\n')
        LOG.flush()
        # Send the embed and shut the bot off
        await ctx.send(embed=embed)
        await bot.close()
        return

    # Add a command to restart the bot
    @commands.command(name="restart", help="Shuts the bot off and then brings it back online", brief="Restarts bot", usage="!restart")
    async def restart(self, ctx):
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
    @commands.command(name="addserver", help="Add a server to the list of servers the bot can be used in", brief="Add a permitted server", usage="!addserver (guild_id)")
    async def add_server(self, ctx, guild_id: typing.Optional[int] = commands.parameter(default=None, description="The ID of the guild to add")):
        global admins, allowed_guilds
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
    
    @commands.command(name="work", help="Start or stop the clock of working on the bot.", usage="!work [start/stop]")
    async def work(self, ctx, clock: str = commands.parameter(description="Whether or not to start or stop working")):
        global start_time
        me = bot.get_user(admins[0])
        if clock == "start":
            start_time = int(time.time())
            await me.send(f"You've 'clocked in' to working on the bot.")
        elif clock == "stop":
            end_time = int(time.time())
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
                        if key == "SECONDS_WORKED":
                            # If it is, then append the guild_id to the current value
                            value = f'{int(value) + (end_time - start_time)}'
                        # Write the key and value to the .env again
                        f.write(f'{key}={value}')
                    except ValueError:
                        # syntax error
                        pass
            await me.send(f"You've 'clocked out' to working on the bot.")
            

    async def cog_check(self, ctx):
        if ctx.message.author.id in admins:
            return True
        embed=discord.Embed(title="Improper Access", description=f'User {ctx.message.author} ({ctx.message.author.id}) does not have permissions to run this command. Contact an Admin to resolve this issue.', color=0xFF5733)
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use command {ctx.command}, but did not have proper access.\n')
        LOG.flush()
        await ctx.send(embed=embed)
        return False
    
    
bot.run(TOKEN)