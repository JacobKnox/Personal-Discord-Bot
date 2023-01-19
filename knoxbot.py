# Python imports
import time # time library
import os # os, mainly used to restart the bot
import sys # sys, mainly used to exit the program when shutting the bot off
import typing # typing, mainly used for command parameters
# ENV related imports
from dotenv import load_dotenv
from os import getenv as ENV
# Path related imports
from os.path import join, dirname
# Discord related imports
import discord
from discord.ext import commands
# Importing my utility files
import utils.pnw_utils as pnw # pnw utility functions
from utils.utils import * # general utility functions
from exceptions import * # custom exceptions

# Load the env from its path
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
# Get important info from the env
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
async def on_ready() -> None:
    global admins, allowed_guilds
    # Call the start function to intialize the global admin and allowed_guilds variables
    admins, allowed_guilds = start(dotenv_path)
    # Tell what guilds (servers) the bot is currently in, just because (might delete later)
    print(f'{bot.user} is connected to the following guilds:')
    for guild in bot.guilds:
        print(f'{guild.name} (id: {guild.id})')
    # Add all of the cog classes to the bot, so commands can be used and categorized in !help
    await bot.add_cog(PoliticsandWar(bot))
    await bot.add_cog(Moderation(bot))
    await bot.add_cog(BotAdmin(bot))
    # Let me know that all of the cogs have been loaded
    print("Bot is ready to use!")

# Event for when a command error occurs
@bot.event
async def on_command_error(ctx: commands.Context, error: Exception) -> None:
    # If the error is that the attempted command does not exist
    if isinstance(error, commands.CommandNotFound):
        # Send a message saying it doesn't exist
        embed = discord.Embed(title="Command Not Found", description=f"The command you attempted to use, {ctx.message.content}, does not currently exist.", color=0xFF5733)
        await ctx.send(embed=embed)
        # Log that the user attempted to use this fictional command
        ERROR_LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use non-existent command: {ctx.message.content}\n')
        ERROR_LOG.flush()
        return
    # If the error is that they attempted to use a command without all of the required arguments
    elif isinstance(error, commands.MissingRequiredArgument):
        # Send a message saying the user missed required arguments
        cmd = bot.get_command(str(ctx.command))
        embed = discord.Embed(title="Missing Argument(s)", description=f"Command usage:\n{cmd.usage}", color=0xFF5733)
        await ctx.send(embed=embed)
        # Log that the user attempted to use the command without the required arguments
        ERROR_LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) improperly used command: {ctx.command}\n')
        ERROR_LOG.flush()
        return
    elif isinstance(error, commands.BadArgument):
        # Send a message saying the user used a bad argument
        cmd = bot.get_command(str(ctx.command))
        embed = discord.Embed(title="Bad Argument(s)", description=f"Command usage:\n{cmd.usage}", color=0xFF5733)
        await ctx.send(embed=embed)
        # Log that the user attempted to use the command without the required arguments
        ERROR_LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) improperly used command: {ctx.command}\n')
        ERROR_LOG.flush()
        return
    # For all other errors, get me (I'm always the first admin) and send me a summary of the error
    me = bot.get_user(admins[0])
    await me.send(f"There has been an error: {error.__class__.__name__}\n{', '.join(error.args)}\nRaised when attempted: {ctx.message.content}")
    # Log the error
    ERROR_LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) caused error {error.__class__.__name__} ({", ".join(error.args)}) with message {ctx.message.content}.\n')
    ERROR_LOG.flush()
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
    async def calc_infra(self, ctx: commands.Context, start: float = commands.parameter(description="Starting infrastructure level"), end: float = commands.parameter(description="Ending instrastructure level"), nation_id: typing.Optional[int] = commands.parameter(default=None, description="ID of the nation to calculate for")) -> None:
        # If the nation_id (an optional parameter) is not set, then calculate the value without their specific info
        if nation_id is None:
            infra_cost = pnw.calculate_infrastructure_value(start, end)
            embed=discord.Embed(title="Calculate Infrastructure Cost", description=f'The cost to go from {start} to {end} is:\n${infra_cost: ,.2f}', color=0xFF5733)
        # Otherwise, calculate it with their specific info
        else:
            # Get the infra query result
            result = pnw.get_query("infra", nation_id)
            infra_cost = pnw.calc_infra_cost(start, end, result)
            embed=discord.Embed(title="Calculate Infrastructure Cost", description=f'The cost to go from {start} to {end} for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}) is:\n${infra_cost: ,.2f}', color=0xFF5733)
        # Log the command usage and send the created embed
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwinfra command.\n')
        LOG.flush()
        await ctx.send(embed=embed)

    # Add a command to calculate the cost to go from one city to another city
    @commands.command(name='pnwcity', help="Calculates the cost to go from one city to another, optionally for a specific nation.", brief="Calculates the cost of cities.", usage="!pnwcity start end (nation_id)")
    async def calc_city(self, ctx: commands.Context, start: int = commands.parameter(description="Starting city level"), end: int = commands.parameter(description="Ending city level"), nation_id: typing.Optional[int] = commands.parameter(default=None, description="ID of the nation to calculate for")) -> None:
        # If the nation_id (an optional parameter) is not set, then calculate the value without their specific info
        if nation_id is None:
            city_cost = pnw.calc_city_cost(start, end)
            embed=discord.Embed(title="Calculate City Cost", description=f'The cost to go from {start} to {end} is:\n${city_cost: ,.2f}', color=0xFF5733)
        # Otherwise, calculate it with their specific info
        else:
            # Get the city query result
            result = pnw.get_query("city", nation_id)
            city_cost = pnw.calc_city_cost(start, end, result)
            embed=discord.Embed(title="Calculate City Cost", description=f'The cost to go from {start} to {end} for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}) is:\n${city_cost: ,.2f}', color=0xFF5733)
        # Log the command usage and send the created embed
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwcity command.\n')
        LOG.flush()
        await ctx.send(embed=embed)


    ####################
    # REVENUE COMMANDS #
    ####################


    # Add a command to calculate food revenue (usage, production, and net revenue) of a nation
    # Users may find a very small margin of error. This is being attributed to constantly fluctuating radiation in Orbis.
    @commands.command(name="pnwfood", help="Calculates the food usage, production, and net revenue for a nation.", brief="Calculates food stats for a nation.", usage="!pnwfood nation_id")
    async def calc_food(self, ctx: commands.Context, nation_id: int = commands.parameter(description="ID of the nation to calculate for")) -> None:
        # Get the food query result
        result = pnw.get_query("food", nation_id)
        # Call the food calculation function
        net_food, food_production, food_usage = pnw.calc_food_rev(result)
        embed=discord.Embed(title="Food Statistics", description=f'Statistics about food revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {abs(food_production): ,.2f}\nUsage: {food_usage: ,.2f}\nNet: {net_food: ,.2f}', color=0xFF5733)
        # Log the command usage and send the created embed
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwfood command with id {nation_id}.\n')
        LOG.flush()
        await ctx.send(embed=embed)
        
    # Add a command to calculate revenue (usage, production, and net revenue) for any raw resource of a nation
    @commands.command(name="pnwraw", help="Calculates the raw's usage, production, and net revenue for a nation.", brief="Calculates raw stats for a nation.", usage="!pnwraw nation_id resource")
    async def calc_raw(self, ctx: commands.Context, nation_id: int = commands.parameter(description="ID of the nation to calculate for"), resource: str = commands.parameter(description="Raw resource to calculate the revenue for")) -> None:
        # Do anything we need to related to resources
        # May get rid of utility function unless I need it for manufactured command and others
        result, flag = await resource_tasks(nation_id)
        if flag:
            return
        # Call the calculation function
        try:
            net, production, usage = pnw.calc_raw_rev(result, resource.lower())
        except InvalidResourceException as inst:
            embed=discord.Embed(title=f"{inst.name}", description=f'{inst.message}', color=0xFF5733)
            await ctx.send(embed=embed)
            return
        embed=discord.Embed(title=f"{resource.capitalize()} Statistics", description=f'Statistics about {resource.lower()} revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {abs(production): ,.2f}\nUsage: {usage: ,.2f}\nNet: {net: ,.2f}', color=0xFF5733)
        # Log the command usage and send the generated embed
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwraw command with id {nation_id} and resource {resource.lower()}.\n')
        LOG.flush()
        await ctx.send(embed=embed)
        
    # Add a command to calculate revenue (usage, production, and net revenue) for any manufactured resource of a nation
    @commands.command(name="pnwmanu", help="Calculates the manufactured's usage, production, and net revenue for a nation.", brief="Calculates manufactured stats for a nation.", usage="!pnwmanu nation_id resource")
    async def calc_manu(self, ctx: commands.Context, nation_id: int = commands.parameter(description="ID of the nation to calculate for"), resource: str = commands.parameter(description="Manufactured resource to calculate the revenue for")) -> None:
        # Do anything we need to related to resources
        # May get rid of utility function unless I need it for manufactured command and others
        result, flag = await resource_tasks(nation_id)
        if flag:
            return
        # Call the calculation function
        try:
            production = pnw.calc_manu_rev(result, resource.lower())
        except InvalidResourceException as inst:
            embed=discord.Embed(title=f"{inst.name}", description=f'{inst.message}', color=0xFF5733)
            await ctx.send(embed=embed)
            return
        embed=discord.Embed(title=f"{resource.capitalize()} Statistics", description=f'Statistics about {resource.lower()} revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {production: ,.2f}\nUsage: {0: ,.2f}\nNet: {production: ,.2f}', color=0xFF5733)
        # Log the command usage and send the generated embed
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwmanu command with id {nation_id} and resource {resource.lower()}.\n')
        LOG.flush()
        await ctx.send(embed=embed)


    #################
    # USER COMMANDS #
    #################


    # WIP command to display user's Politics and War information
    @commands.command(name="mypnwinfo", enabled=False)
    async def my_info(self, ctx: commands.Context, nation_id: int = commands.parameter(description="ID of the nation whose information is to be displayed"), api_key: typing.Optional[str]=commands.parameter(default=None, description="User's API key, used to access their personal information for display")) -> None:
        await ctx.message.delete()
        # If they specified an API key, then they want to display sensitive information
        if api_key is not None:
            result = pnw.get_query("my_info", nation_id, api_key)
            nation = result.nations[0]
            embed=discord.Embed(title=f'Info for {nation.nation_name}',description=f'Military\nSoldiers: {nation.soldiers}\nTanks: {nation.tanks}\nAircraft: {nation.aircraft}\nShips: {nation.ships}', color=0xFF5733)
        # Otherwise, they only want to display non-sensitive information
        else:
            result = pnw.get_query("my_info", nation_id)
            nation = result.nations[0]
            embed=discord.Embed(title=f'Info for {nation.nation_name}',description=f'Military\nSoldiers: {nation.soldiers}\nTanks: {nation.tanks}\nAircraft: {nation.aircraft}\nShips: {nation.ships}', color=0xFF5733)
        # Log the command usage
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !mypnwinfo command with id {nation_id}.\n')
        LOG.flush()
        await ctx.send(embed=embed)
    
    # Add cog check that simply calls the general_tasks utility function to check a few things
    async def cog_check(self, ctx: commands.Context) -> bool:
        return await generic_tasks(LOG, ctx, allowed_guilds)




################
#              #
# MOD COMMANDS #
#              #
################
class Moderation(commands.Cog, description="Moderation commands"):
    # WIP ban command for moderators to ban users
    @commands.command(name="ban", enabled=False, help="Ban one or more user(s) with a specified reason", brief="Ban people", usage="!ban @Jacob @Wumpus Bad people")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, members: commands.Greedy[discord.Member] = commands.parameter(description="User(s) to ban"), *, reason: typing.Optional[str] = commands.parameter(default=None, description="Reason for banning the user(s)")) -> None:
        for member in members:
            await member.ban(reason = reason)
        embed = discord.Embed(title="Wall of Bans", description=f"The following Discord users have joined the Wall of Bans of {ctx.guild.name} for the reason '{reason}':\n{', '.join(f'{member.name} ({member.id})' for member in members)}", color=0xFF5733)
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !ban command to ban {", ".join(f"{member.name} ({member.id})" for member in members)} for the reason "{reason}".\n')
        LOG.flush()
        await ctx.send(embed=embed)
    
    # Add cog check that simply calls the general_tasks utility function to check a few things
    async def cog_check(self, ctx: commands.Context) -> bool:
        return await generic_tasks(LOG, ctx, allowed_guilds)





######################
#                    #
# BOT ADMIN COMMANDS #
#                    #
######################
class BotAdmin(commands.Cog, name="Bot Admin", description="Commands for admins of the bot"):
    # Add a command to clear the logs
    @commands.command(name="clearlog", help="Clears all of the logs associated with the bot", brief="Clears logs", usage="!clearlogs")
    async def clear_log(self, ctx: commands.Context) -> None:
        # Clear the command log by opening and passing it
        with open(ENV('LOG_DIRECTORY'),'w') as _:
            pass
        # Clear the error log in a similar way
        with open(ENV('ERROR_LOG_DIRECTORY'),'w') as _:
            pass
        # Send a message and log that the logs have been cleared
        embed=discord.Embed(title="Log Clear", description=f'Admin {ctx.message.author} ({ctx.message.author.id}) has cleared the logs.', color=0xFF5733)
        LOG.write(f'Admin {ctx.message.author} ({ctx.message.author.id}) has cleared the logs.')
        LOG.flush()
        await ctx.send(embed=embed)

    # Add a command to shut the bot off
    @commands.command(name="shutoff", help="Shuts the bot off completly", brief="Shut bot off", usage="!shutoff")
    async def shutoff(self, ctx: commands.Context) -> None:
        # Create an embed saying that the bot was shut off by this specific admin
        embed=discord.Embed(title="Bot Shutoff", description=f'Admin {ctx.message.author} ({ctx.message.author.id}) has shutoff the bot.', color=0xFF5733)
        # Write to the log that the bot was shut off and send the embed
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) shut the bot off.\n')
        LOG.flush()
        await ctx.send(embed=embed)
        # Close the bot and exit the program
        await bot.close()
        sys.exit()

    # Add a command to restart the bot
    @commands.command(name="restart", help="Shuts the bot off and then brings it back online", brief="Restarts bot", usage="!restart")
    async def restart(self, ctx: commands.Context) -> None:
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
    async def add_server(self, ctx: commands.Context, guild_id: typing.Optional[int] = commands.parameter(default=None, description="The ID of the guild to add")) -> None:
        global admins, allowed_guilds
        # If the user does not specify a guild_id, then they want to add the server they used the command in
        if guild_id is None:
            guild_id = ctx.guild.id
        # Check if the guild is already a permitted guild
        if check_guild(ctx.guild, allowed_guilds):
            # Log and message telling that it is
            embed=discord.Embed(title="Already Permitted", description=f'Server {guild_id} is already an allowed server for bot commands.', color=0xFF5733)
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
                    # In the event of an error, just write the whole file again so as to not delete parts of the .env
                    f.write(line)
                    pass
            # If the key is not found, then there are no allowed guilds yet, so it needs to be added to the .env
            if not found:
                f.write(f'\nALLOWED_GUILDS={guild_id}')
        # Re-assign the admins and allowed_guilds variables to account for the changes to the .env
        admins, allowed_guilds = start(dotenv_path)
        # Create an embed saying that the server was added successfully, log it, and send it
        embed=discord.Embed(title="Server Added", description=f"Admin {ctx.message.author} ({ctx.message.author.id}) has added the guild {guild_id} to the bot's permitted guilds.", color=0xFF5733)
        LOG.write(f"Admin {ctx.message.author} ({ctx.message.author.id}) has added the guild {guild_id} to the bot's permitted guilds.")
        LOG.flush()
        await ctx.send(embed=embed)
    
    # Add a command where I can try to keep track of how much time I spend working on the bot
    @commands.command(name="work", help="Start or stop the clock of working on the bot.", usage="!work [start/stop]")
    async def work(self, ctx: commands.Context, clock: str = commands.parameter(description="Whether or not to start or stop working")) -> None:
        global start_time
        # Get me (the first admin)
        me = bot.get_user(admins[0])
        # If the clock status is start, then set the start time and message me saying I clocked in
        if clock == "start":
            start_time = int(time.time())
            await me.send(f"You've 'clocked in' to working on the bot.")
        # Otherwise, if it is stop, the set the end time
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
                        # Check if the key is SECONDS_WORKED
                        if key == "SECONDS_WORKED":
                            # If it is, then calculate the difference between the end time and the start time then add it to the current value
                            value = f'{int(value) + (end_time - start_time)}'
                        # Write the key and value to the .env again
                        f.write(f'{key}={value}')
                    except ValueError:
                        # In the event of an error, just write the whole file again so as to not delete parts of the .env
                        f.write(line)
                        pass
            # Message me letting me know I clocked out
            await me.send(f"You've 'clocked out' to working on the bot.")
            
    # Add a cog check that checks if the user of these commands is an admin
    async def cog_check(self, ctx: commands.Context) -> bool:
        # If they're an admin, then it simply returns true
        if ctx.message.author.id in admins:
            return True
        # Otherwise, it messages and logs that a non-admin tried to use the command before returning false
        embed=discord.Embed(title="Improper Access", description=f'User {ctx.message.author} ({ctx.message.author.id}) does not have permissions to run this command. Contact an Admin to resolve this issue.', color=0xFF5733)
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use command {ctx.command}, but did not have proper access.\n')
        LOG.flush()
        await ctx.send(embed=embed)
        return False
    
# Run the bot
bot.run(TOKEN)