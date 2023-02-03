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

#Initialize the bot with a set prefix of ! and all possible Intents
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

errors: list[Exception] = []

# Load the env from its path
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
# Get important info from the env
TOKEN = ENV("DISCORD_TOKEN")
if not TOKEN or TOKEN == '':
    raise NoTokenException()
try:
    LOG = open(ENV('LOG_DIRECTORY'), "a")
except OSError as inst:
    inst.message = "Could not open LOG."
    errors.append(inst)
    pass
except TypeError as inst:
    inst.message = "No file provided for LOG."
    errors.append(inst)
    pass
try:
    ERROR_LOG = open(ENV('ERROR_LOG_DIRECTORY'), "a")
except OSError as inst:
    inst.message = "Could not open ERROR_LOG."
    errors.append(inst)
    pass
except TypeError as inst:
    inst.message = "No file provided for ERROR_LOG."
    errors.append(inst)
    pass
start_time = 0





##############
#            #
# BOT EVENTS #
#            #
##############





# Event for when the bot is ready
@bot.event
async def on_ready() -> None:
    global admins, allowed_guilds
    admins = []
    allowed_guilds = []
    # Call the start function to intialize the global admin and allowed_guilds variables
    admins, allowed_guilds, start_errors = start(dotenv_path)
    for error in start_errors:
        errors.append(error)
    if errors:
        if admins:
            me = bot.get_user(admins[0])
            for error in errors:
                await attempt_send(me, f"There has been an error: {error.__class__.__name__}\n{error.message}")
        else:
            raise errors[0]
        await bot.close()
        sys.exit()
    # Tell what guilds (servers) the bot is currently in, just because (might delete later)
    print(f'{bot.user} is connected to the following guilds:')
    for guild in bot.guilds:
        print(f'{guild.name} (id: {guild.id})')
    # Add all of the cog classes to the bot, so commands can be used and categorized in !help
    try:
        await bot.add_cog(PoliticsandWar(bot))
        await bot.add_cog(Moderation(bot))
        await bot.add_cog(BotAdmin(bot))
    except Exception as inst:
        me: discord.User = bot.get_user(admins[0])
        await attempt_send(me, f"There has been an error: {inst.__class__.__name__}\n{', '.join(inst.args)}")
        await bot.close()
        sys.exit()
    # Let me know that all of the cogs have been loaded
    print("Bot is ready to use!")

# Event for when a command error occurs
@bot.event
async def on_command_error(ctx: commands.Context,
                           error: Exception
                           ) -> None:
    #raise error
    # If the error is that the attempted command does not exist
    if isinstance(error, commands.CommandNotFound):
        # Send a message saying it doesn't exist
        embed = discord.Embed(title="Command Not Found", description=f"The command you attempted to use, {ctx.message.content}, does not currently exist.", color=0xFF5733)
        await attempt_send(ctx, embed)
        # Log that the user attempted to use this fictional command
        ERROR_LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use non-existent command: {ctx.message.content}\n')
        ERROR_LOG.flush()
        return
    # If the error is that they attempted to use a command without all of the required arguments
    elif isinstance(error, commands.MissingRequiredArgument):
        # Send a message saying the user missed required arguments
        cmd = bot.get_command(str(ctx.command))
        embed = discord.Embed(title="Missing Argument(s)", description=f"Command usage:\n{cmd.usage}", color=0xFF5733)
        await attempt_send(ctx, embed)
        # Log that the user attempted to use the command without the required arguments
        ERROR_LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) improperly used command: {ctx.command}\n')
        ERROR_LOG.flush()
        return
    elif isinstance(error, commands.BadArgument):
        # Send a message saying the user used a bad argument
        cmd = bot.get_command(str(ctx.command))
        embed = discord.Embed(title="Bad Argument(s)", description=f"Command usage:\n{cmd.usage}", color=0xFF5733)
        await attempt_send(ctx, embed)
        # Log that the user attempted to use the command without the required arguments
        ERROR_LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) improperly used command: {ctx.command}\n')
        ERROR_LOG.flush()
        return
    elif isinstance(error, commands.DisabledCommand):
        # Send a message saying the user used attempted to use a disabled command
        embed = discord.Embed(title="Disabled Command", description=f"The command {ctx.command} is currently disabled.", color=0xFF5733)
        await attempt_send(ctx, embed)
        # Log that the user attempted to use the disabled command
        ERROR_LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use disabled command: {ctx.command}\n')
        ERROR_LOG.flush()
        return
    elif isinstance(error, commands.CommandInvokeError):
        flag = False
        # Send a message saying something went wrong when the user attempted to use the command
        if "Command raised an exception: " in error.args[0]:
            flag = True
            embed = discord.Embed(title="Error in Command Invocation", description=f"Something went wrong when you used the command {ctx.command}\n{error.args[0][29:]}", color=0xFF5733)
        else:
            embed = discord.Embed(title="Error in Command Invocation", description=f"Something went wrong when you used the command {ctx.command}. The information has been sent to the owner.", color=0xFF5733)
        await attempt_send(ctx, embed)
        # Log that something went wrong
        ERROR_LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use the command: {ctx.command} and got errors: {", ".join(error.args)}\n')
        ERROR_LOG.flush()
        if flag:
            return
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title=f'{error.__class__.__name__}', description=f'{", ".join(error.args)}')
        await attempt_send(ctx, embed)
        return
    elif isinstance(error, commands.CheckFailure):
        return
    # For all other errors, get me (I'm always the first admin) and send me a summary of the error
    me = bot.get_user(admins[0])
    await attempt_send(me, f"There has been an error: {error.__class__.__name__}\n{', '.join(error.args)}\nRaised when attempted: {ctx.message.content}")
    # Log the error
    ERROR_LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) caused error {error.__class__.__name__} ({", ".join(error.args)}) with message {ctx.message.content}.\n')
    ERROR_LOG.flush()
    #raise error





#############################
#                           #
# POLITICS AND WAR COMMANDS #
#                           #
#############################
class PoliticsandWar(commands.Cog,
                     name="Politics and War",
                     description="All commands related to the Politics and War browser game."):
    ########################
    # CALCULATION COMMANDS #
    ########################


    # Add a command to calculate the cost of infrastructure
    @commands.command(name='pnwinfra',
                      help="Calculates the cost to go from one level of infrastructure to another, optionally for a specific nation.",
                      brief="Calculates cost of infrastrucutre.",
                      usage="!pnwinfra start end (nation_id)")
    async def calc_infra(self,
                         ctx: commands.Context,
                         start: float = commands.parameter(description="Starting infrastructure level"),
                         end: float = commands.parameter(description="Ending instrastructure level"),
                         nation_id: typing.Optional[int] = commands.parameter(default=None, description="ID of the nation to calculate for")
                         ) -> None:
        # If the nation_id (an optional parameter) is not set, then calculate the value without their specific info
        if nation_id is None:
            infra_cost = pnw.calculate_infrastructure_value(start, end)
            embed = discord.Embed(title="Calculate Infrastructure Cost", description=f'The cost to go from {start} to {end} is:\n${infra_cost: ,.2f}', color=0xFF5733)
        # Otherwise, calculate it with their specific info
        else:
            # Get the infra query result
            result = pnw.get_query("infraland", nation_id)
            infra_cost = pnw.calc_infra_cost(start, end, result)
            embed = discord.Embed(title="Calculate Infrastructure Cost", description=f'The cost to go from {start} to {end} for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}) is:\n${infra_cost: ,.2f}', color=0xFF5733)
        # Log the command usage and send the created embed
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwinfra command.\n')
        LOG.flush()
        await attempt_send(ctx, embed)
        
    # Add a command to calculate the cost of infrastructure
    @commands.command(name='pnwland',
                      help="Calculates the cost to go from one level of land to another, optionally for a specific nation.",
                      brief="Calculates cost of land.",
                      usage="!pnwland start end (nation_id)")
    async def calc_land(self,
                        ctx: commands.Context, 
                        start: float = commands.parameter(description="Starting land level"),
                        end: float = commands.parameter(description="Ending land level"),
                        nation_id: typing.Optional[int] = commands.parameter(default=None, description="ID of the nation to calculate for")
                        ) -> None:
        # If the nation_id (an optional parameter) is not set, then calculate the value without their specific info
        if nation_id is None:
            land_cost = pnw.calculate_land_value(start, end)
            embed = discord.Embed(title="Calculate Land Cost", description=f'The cost to go from {start} to {end} is:\n${land_cost: ,.2f}', color=0xFF5733)
        # Otherwise, calculate it with their specific info
        else:
            # Get the infra query result
            result = pnw.get_query("infraland", nation_id)
            land_cost = pnw.calc_land_cost(start, end, result)
            embed = discord.Embed(title="Calculate Land Cost", description=f'The cost to go from {start} to {end} for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}) is:\n${land_cost: ,.2f}', color=0xFF5733)
        # Log the command usage and send the created embed
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwland command.\n')
        LOG.flush()
        await attempt_send(ctx, embed)

    # Add a command to calculate the cost to go from one city to another city
    @commands.command(name='pnwcity',
                      help="Calculates the cost to go from one city to another, optionally for a specific nation.",
                      brief="Calculates the cost of cities.",
                      usage="!pnwcity start end (nation_id)")
    async def calc_city(self,
                        ctx: commands.Context,
                        start: int = commands.parameter(description="Starting city level"),
                        end: int = commands.parameter(description="Ending city level"),
                        nation_id: typing.Optional[int] = commands.parameter(default=None, description="ID of the nation to calculate for")
                        ) -> None:
        # If the nation_id (an optional parameter) is not set, then calculate the value without their specific info
        if nation_id is None:
            city_cost = pnw.calc_city_cost(start, end)
            embed = discord.Embed(title="Calculate City Cost", description=f'The cost to go from {start} to {end} is:\n${city_cost: ,.2f}', color=0xFF5733)
        # Otherwise, calculate it with their specific info
        else:
            # Get the city query result
            result = pnw.get_query("city", nation_id)
            city_cost = pnw.calc_city_cost(start, end, result)
            embed = discord.Embed(title="Calculate City Cost", description=f'The cost to go from {start} to {end} for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}) is:\n${city_cost: ,.2f}', color=0xFF5733)
        # Log the command usage and send the created embed
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwcity command.\n')
        LOG.flush()
        await attempt_send(ctx, embed)


    ####################
    # REVENUE COMMANDS #
    ####################


    # Add a command to calculate food revenue (usage, production, and net revenue) of a nation
    # Users may find a very small margin of error. This is being attributed to constantly fluctuating radiation in Orbis.
    @commands.command(name="pnwfood",
                      help="Calculates the food usage, production, and net revenue for a nation.",
                      brief="Calculates food stats for a nation.",
                      usage="!pnwfood nation_id")
    async def calc_food(self,
                        ctx: commands.Context,
                        nation_id: int = commands.parameter(description="ID of the nation to calculate for")
                        ) -> None:
        # Get the food query result
        result = pnw.get_query("food", nation_id)
        # Call the food calculation function
        net_food, food_production, food_usage = pnw.calc_food_rev(result)
        embed = discord.Embed(title="Food Statistics", description=f'Statistics about food revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {abs(food_production): ,.2f}\nUsage: {food_usage: ,.2f}\nNet: {net_food: ,.2f}', color=0xFF5733)
        # Log the command usage and send the created embed
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwfood command with id {nation_id}.\n')
        LOG.flush()
        await attempt_send(ctx, embed)
        
    # Add a command to calculate revenue (usage, production, and net revenue) for any raw resource of a nation
    @commands.command(name="pnwraw",
                      help="Calculates the raw's usage, production, and net revenue for a nation.",
                      brief="Calculates raw stats for a nation.",
                      usage="!pnwraw nation_id resource")
    async def calc_raw(self,
                       ctx: commands.Context,
                       nation_id: int = commands.parameter(description="ID of the nation to calculate for"),
                       resource: str = commands.parameter(default="all", description="Raw resource to calculate the revenue for")
                       ) -> None:
        # Do anything we need to related to resources
        # May get rid of utility function unless I need it for manufactured command and others
        result, flag = await resource_tasks(nation_id, ctx)
        if flag:
            return
        # Call the calculation function
        if resource.lower() == "all":
            resources = {"coal": None, "oil": None, "iron": None, "lead": None, "bauxite": None, "uranium": None}
            for resource in resources:
                try:
                    resources[resource] = pnw.calc_raw_rev(result, resource)
                except InvalidResourceException as inst:
                    embed = discord.Embed(title=f"{inst.name}", description=f'{inst.message}', color=0xFF5733)
                    await attempt_send(ctx, embed)
                    return
            embed = discord.Embed(title="All Raw Resource Statistics", description="\n".join(f'{"**" + key.capitalize() + "**"}\nProduction: {value[1]: ,.2f}\nUsage: {abs(value[2]): ,.2f}\nNet: {value[0]: ,.2f}\n' for key, value in resources.items()), color=0xFF5733)
        else:
            try:
                net, production, usage = pnw.calc_raw_rev(result, resource.lower())
            except InvalidResourceException as inst:
                embed = discord.Embed(title=f"{inst.name}", description=f'{inst.message}', color=0xFF5733)
                await attempt_send(ctx, embed)
                return
            embed = discord.Embed(title=f"{resource.capitalize()} Statistics", description=f'Statistics about {resource.lower()} revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {abs(production): ,.2f}\nUsage: {usage: ,.2f}\nNet: {net: ,.2f}', color=0xFF5733)
        # Log the command usage and send the generated embed
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwraw command with id {nation_id} and resource {resource.lower()}.\n')
        LOG.flush()
        await attempt_send(ctx, embed)
        
    # Add a command to calculate revenue (usage, production, and net revenue) for any manufactured resource of a nation
    @commands.command(name="pnwmanu",
                      help="Calculates the manufactured's usage, production, and net revenue for a nation.",
                      brief="Calculates manufactured stats for a nation.",
                      usage="!pnwmanu nation_id resource")
    async def calc_manu(self,
                        ctx: commands.Context,
                        nation_id: int = commands.parameter(description="ID of the nation to calculate for"),
                        resource: str = commands.parameter(default="all", description="Manufactured resource to calculate the revenue for")
                        ) -> None:
        # Do anything we need to related to resources
        # May get rid of utility function unless I need it for manufactured command and others
        result, flag = await resource_tasks(nation_id, ctx)
        if flag:
            return
        # Call the calculation function
        if resource.lower() == "all":
            resources = {"steel": None, "aluminum": None, "gasoline": None, "munitions": None}
            for resource in resources:
                resources[resource] = pnw.calc_manu_rev(result, resource)
            embed = discord.Embed(title="All Manufactured Resource Statistics", description="\n".join(f'{"**" + key.capitalize() + "**"}\nProduction: {value: ,.2f}\nUsage: {0: ,.2f}\nNet: {value: ,.2f}\n' for key, value in resources.items()), color=0xFF5733)
        else:
            try:
                production = pnw.calc_manu_rev(result, resource.lower())
            except InvalidResourceException as inst:
                embed = discord.Embed(title=f"{inst.name}", description=f'{inst.message}', color=0xFF5733)
                await attempt_send(ctx, embed)
                return
            embed = discord.Embed(title=f"{resource.capitalize()} Statistics", description=f'Statistics about {resource.lower()} revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {production: ,.2f}\nUsage: {0: ,.2f}\nNet: {production: ,.2f}', color=0xFF5733)
        # Log the command usage and send the generated embed
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !pnwmanu command with id {nation_id} and resource {resource.lower()}.\n')
        LOG.flush()
        await attempt_send(ctx, embed)
        
    @commands.command(name="treasures",
                      enabled=False)
    async def treasures(self,
                        ctx):
        result = pnw.get_query("treasure")
        greens = [treasure for treasure in result.treasures if (treasure.color == "green" or treasure.color == "any")]
        for treasure in greens:
            print(treasure.color)
    
    @commands.command(name="pnwmarket",
                      help="Returns the lowest sell offer and highest buy offer for a given resource.",
                      brief="Returns market information for a resource.",
                      usage="!pnwmarket resource")
    async def market_info(self,
                          ctx: commands.Context,
                          resource: str = commands.parameter(default="all", description="Resource to get the market information for")
                          ) -> None:
        if resource.lower() == "all":
            resources = {"food": None, "coal": None, "oil": None, "iron": None, "lead": None, "bauxite": None, "uranium": None, "steel": None, "aluminum": None, "gasoline": None, "munitions": None}
            for resource in resources:
                resources[resource] = pnw.market_info(resource)
            embed = discord.Embed(title="All Market Information", description="\n".join(f'{"**" + key.capitalize() + "**"}\nLowest Sell Offer: {value[1]: ,d}\nHighest Buy Offer: {value[0]: ,d}\n' for key, value in resources.items()), color=0xFF5733)
        else:
            try:
                high_buy, low_sell = pnw.market_info(resource)
            except InvalidResourceException as inst:
                    embed = discord.Embed(title=f"{inst.name}", description=f'{inst.message}', color=0xFF5733)
                    await attempt_send(ctx, embed)
                    return
            embed = discord.Embed(title=f'{resource.capitalize()} Market Information', description=f'Lowest Sell Offer: {low_sell: ,d}\nHighest Buy Offer: {high_buy: ,d}')
        await attempt_send(ctx, embed)


    #################
    # USER COMMANDS #
    #################


    # WIP command to display user's Politics and War information
    @commands.command(name="mypnwinfo",
                      enabled=False)
    async def my_info(self,
                      ctx: commands.Context,
                      nation_id: int = commands.parameter(description="ID of the nation whose information is to be displayed"),
                      api_key: typing.Optional[str]=commands.parameter(default=None, description="User's API key, used to access their personal information for display")
                      ) -> None:
        await ctx.message.delete()
        # If they specified an API key, then they want to display sensitive information
        if api_key is not None:
            result = pnw.get_query("my_info", nation_id, api_key)
            nation = result.nations[0]
            embed = discord.Embed(title=f'Info for {nation.nation_name}',description=f'Military\nSoldiers: {nation.soldiers}\nTanks: {nation.tanks}\nAircraft: {nation.aircraft}\nShips: {nation.ships}', color=0xFF5733)
        # Otherwise, they only want to display non-sensitive information
        else:
            result = pnw.get_query("my_info", nation_id)
            nation = result.nations[0]
            embed = discord.Embed(title=f'Info for {nation.nation_name}',description=f'Military\nSoldiers: {nation.soldiers}\nTanks: {nation.tanks}\nAircraft: {nation.aircraft}\nShips: {nation.ships}', color=0xFF5733)
        # Log the command usage
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !mypnwinfo command with id {nation_id}.\n')
        LOG.flush()
        await attempt_send(ctx, embed)
    
    # Add cog check that simply calls the general_tasks utility function to check a few things
    async def cog_check(self,
                        ctx: commands.Context
                        ) -> bool:
        return await generic_tasks(LOG, ctx, allowed_guilds)




################
#              #
# MOD COMMANDS #
#              #
################
class Moderation(commands.Cog,
                 description="Moderation commands"):
    # Ban command for moderators to ban users
    @commands.command(name="ban",
                      help="Ban one or more user(s) with a specified reason",
                      brief="Ban people",
                      usage="!ban @Jacob @Wumpus Bad people")
    @commands.has_permissions(ban_members=True)
    async def ban(self,
                  ctx: commands.Context,
                  members: commands.Greedy[discord.Member] = commands.parameter(description="User(s) to ban"),
                  *,
                  reason: typing.Optional[str] = commands.parameter(default="No reason given", description="Reason for banning the user(s)")
                  ) -> None:
        if members is None:
            await attempt_send(ctx, "You must specify which members to ban.")
            return
        for member in members:
            await member.ban(reason = reason)
        embed = discord.Embed(title="Wall of Bans", description=f'The following Discord users have joined the Wall of Bans of {ctx.guild.name} for the reason "{reason}":\n{"".join(f"{member.name} ({member.id})"for member in members)}\n', color=0xFF5733)
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !ban command to ban {", ".join(f"{member.name} ({member.id})" for member in members)} for the reason "{reason}".\n')
        LOG.flush()
        await attempt_send(ctx, embed)
        
    @commands.command(name="kick",
                      help="Kick one or more user(s) with a specified reason",
                      brief="Kick people",
                      usage="!kick @Jacob @Wumpus Bad people")
    @commands.has_permissions(kick_members=True)
    async def kick(self,
                  ctx: commands.Context,
                  members: commands.Greedy[discord.Member] = commands.parameter(description="User(s) to kick"),
                  *,
                  reason: typing.Optional[str] = commands.parameter(default="No reason given", description="Reason for kicking the user(s)")
                  ) -> None:
        if members is None:
            await attempt_send(ctx, "You must specify which members to kick.")
            return
        for member in members:
            await member.ban(reason = reason)
        embed = discord.Embed(title="Wall of Kicks", description=f'The following Discord users have joined the Wall of Kicks of {ctx.guild.name} for the reason "{reason}":\n{"".join(f"{member.name} ({member.id})"for member in members)}\n', color=0xFF5733)
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !kick command to kick {", ".join(f"{member.name} ({member.id})" for member in members)} for the reason "{reason}".\n')
        LOG.flush()
        await attempt_send(ctx, embed)
    
    @commands.command(name="mute",
                      help="Mute one or more user(s)",
                      brief="Mute people",
                      usage="!mute @Jacob @Wumpus")
    @commands.has_permissions(moderate_members=True, manage_roles=True)
    async def mute(self,
                   ctx: commands.Context,
                   members: commands.Greedy[discord.Member] = commands.parameter(description="User(s) to mute"),
                   ) -> None:
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            perms = discord.Permissions.none() or discord.Permissions(read_messages=True, read_message_history=True)
            role = await ctx.guild.create_role(name="Muted", permissions=perms, colour=discord.Colour(0x0062ff))
        for member in members:
            if role in member.roles:
                await attempt_send(ctx, f'Member {member.name} ({member.id}) is already muted.')
                continue
            await member.add_roles(role)
            await attempt_send(ctx, f'Member {member.name} ({member.id}) has been muted.')
    
    @commands.command(name="unmute",
                      help="Unmute one or more user(s)",
                      brief="Unmute people",
                      usage="!unmute @Jacob @Wumpus")
    @commands.has_permissions(moderate_members=True, manage_roles=True)
    async def unmute(self,
                   ctx: commands.Context,
                   members: commands.Greedy[discord.Member] = commands.parameter(description="User(s) to unmute"),
                   ) -> None:
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            await attempt_send(ctx, f'Cannot unmute a member when the Muted role does not exist yet.')
        for member in members:
            if role not in member.roles:
                await attempt_send(ctx, f'Member {member.name} ({member.id}) does not have the Muted role.')
                continue
            await member.remove_roles(role)
            await attempt_send(ctx, f'Member {member.name} ({member.id}) has been unmuted.')
        
    
    # Add cog check that simply calls the general_tasks utility function to check a few things
    async def cog_check(self,
                        ctx: commands.Context
                        ) -> bool:
        return await generic_tasks(LOG, ctx, allowed_guilds)





######################
#                    #
# BOT ADMIN COMMANDS #
#                    #
######################
class BotAdmin(commands.Cog,
               name="Bot Admin",
               description="Commands for admins of the bot"):
    # Add a command to clear the logs
    @commands.command(name="clearlog",
                      help="Clears all of the logs associated with the bot",
                      brief="Clears logs",
                      usage="!clearlogs")
    async def clear_log(self,
                        ctx: commands.Context
                        ) -> None:
        # Clear the command log by opening and passing it
        with open(ENV('LOG_DIRECTORY'),'w') as _:
            pass
        # Clear the error log in a similar way
        with open(ENV('ERROR_LOG_DIRECTORY'),'w') as _:
            pass
        # Send a message and log that the logs have been cleared
        embed = discord.Embed(title="Log Clear", description=f'Admin {ctx.message.author} ({ctx.message.author.id}) has cleared the logs.', color=0xFF5733)
        LOG.write(f'Admin {ctx.message.author} ({ctx.message.author.id}) has cleared the logs.')
        LOG.flush()
        await attempt_send(ctx, embed)

    # Add a command to shut the bot off
    @commands.command(name="shutoff",
                      help="Shuts the bot off completly",
                      brief="Shut bot off",
                      usage="!shutoff")
    async def shutoff(self,
                      ctx: commands.Context
                      ) -> None:
        # Create an embed saying that the bot was shut off by this specific admin
        embed = discord.Embed(title="Bot Shutoff", description=f'Admin {ctx.message.author} ({ctx.message.author.id}) has shutoff the bot.', color=0xFF5733)
        # Write to the log that the bot was shut off and send the embed
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) shut the bot off.\n')
        LOG.flush()
        await attempt_send(ctx, embed)
        # Close the bot and exit the program
        await bot.close()
        sys.exit()

    # Add a command to restart the bot
    @commands.command(name="restart",
                      help="Shuts the bot off and then brings it back online",
                      brief="Restarts bot",
                      usage="!restart")
    async def restart(self,
                      ctx: commands.Context
                      ) -> None:
        # Create an embed saying that the bot was restart by this specific admin
        embed = discord.Embed(title="Bot Restart", description=f'Admin {ctx.message.author} ({ctx.message.author.id}) has restarted the bot.', color=0xFF5733)
        # Write to the log that the bot was restart
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) restarted the bot.\n')
        LOG.flush()
        # Send the embed
        await attempt_send(ctx, embed)
        # Re-execute this file to restart the bot
        os.execv(sys.executable, ['python'] + sys.argv)
        
    # Add a command to add a server to the permitted list of servers
    @commands.command(name="addserver",
                      help="Add a server to the list of servers the bot can be used in",
                      brief="Add a permitted server",
                      usage="!addserver (guild_id)")
    async def add_server(self,
                         ctx: commands.Context,
                         guild_id: typing.Optional[int] = commands.parameter(default=None, description="The ID of the guild to add")
                         ) -> None:
        global admins, allowed_guilds
        # If the user does not specify a guild_id, then they want to add the server they used the command in
        if guild_id is None:
            guild_id = ctx.guild.id
        # Check if the guild is already a permitted guild
        if check_guild(ctx.guild, allowed_guilds):
            # Log and message telling that it is
            embed = discord.Embed(title="Already Permitted", description=f'Server {guild_id} is already an allowed server for bot commands.', color=0xFF5733)
            LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to add server {guild_id}, but that server already has permission.\n')
            LOG.flush()
            await attempt_send(ctx, embed)
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
        embed = discord.Embed(title="Server Added", description=f"Admin {ctx.message.author} ({ctx.message.author.id}) has added the guild {guild_id} to the bot's permitted guilds.", color=0xFF5733)
        LOG.write(f"Admin {ctx.message.author} ({ctx.message.author.id}) has added the guild {guild_id} to the bot's permitted guilds.")
        LOG.flush()
        await attempt_send(ctx, embed)
    
    # Add a command where I can try to keep track of how much time I spend working on the bot
    @commands.command(name="work",
                      help="Start or stop the clock of working on the bot.",
                      usage="!work [start/stop]")
    async def work(self,
                   ctx: commands.Context,
                   clock: str = commands.parameter(description="Whether or not to start or stop working")
                   ) -> None:
        global start_time
        # Get me (the first admin)
        me = bot.get_user(admins[0])
        # If the clock status is start, then set the start time and message me saying I clocked in
        if clock == "start":
            start_time = int(time.time())
            await attempt_send(me, f"You've 'clocked in' to working on the bot.")
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
            await attempt_send(me, f"You've 'clocked out' to working on the bot.")
            
    # Add a cog check that checks if the user of these commands is an admin
    async def cog_check(self,
                        ctx: commands.Context
                        ) -> bool:
        # If they're an admin, then it simply returns true
        if ctx.message.author.id in admins:
            return True
        # Otherwise, it messages and logs that a non-admin tried to use the command before returning false
        embed = discord.Embed(title="Improper Access", description=f'User {ctx.message.author} ({ctx.message.author.id}) does not have permissions to run this command. Contact an Admin to resolve this issue.', color=0xFF5733)
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use command {ctx.command}, but did not have proper access.\n')
        LOG.flush()
        await attempt_send(ctx, embed)
        return False
    
# Run the bot
bot.run(TOKEN)