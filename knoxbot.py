from os import getenv as ENV
from os.path import join, dirname
import discord
from dotenv import load_dotenv
from discord.ext import commands
import utils.pnw_utils as pnw

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
TOKEN = ENV("DISCORD_TOKEN")
GUILD = ENV('DISCORD_GUILD')
LOG = open("commands_log.log", "a")

def start():
    global admins, allowed_guilds
    admins = None
    allowed_guilds = None
    with open(dotenv_path, "r") as f:
        for line in f.readlines():
            line = line.split("=")
            if(line[0] == "ADMIN_IDS"):  
                admins = [int(id) for id in line[1].split(",")]
            elif(line[0] == "ALLOWED_GUILDS"):
                allowed_guilds = [int(id) for id in line[1].split(",")]
    print(allowed_guilds)

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    start()
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name} (id: {guild.id})'
    )
    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')

def check_guild(guild):
    if guild.id in allowed_guilds:
        return True
    else:
        return False
    
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Oops... that command doesn't exist.")
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use command: {ctx.message.content}\n')
        LOG.flush()
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
    if not check_guild(ctx.guild):
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
    if not check_guild(ctx.guild):
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
    if not check_guild(ctx.guild):
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
    if not check_guild(ctx.guild):
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
async def my_info(ctx, nation_id, api_key):
    await ctx.message.delete()
    result = pnw.get_query("my_info", nation_id, api_key)
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
        embed=discord.Embed(title="Bot Shutoff", description=f'Admin {ctx.message.author} ({ctx.message.author.id}) has shutoff the bot.', color=0xFF5733)
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) shut the bot off.\n')
        LOG.flush()
        await ctx.send(embed=embed)
        await bot.close()
    # Otherwise, send an improper access message
    else:
        embed=discord.Embed(title="Improper Access", description=f'User {ctx.message.author} ({ctx.message.author.id}) does not have permissions to run this command. Contact an Admin to resolve this issue.', color=0xFF5733)
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to shut off the bot, but did not have proper access.\n')
        LOG.flush()
        await ctx.send(embed=embed)

@bot.command(name="addserver")
async def add_server(ctx):
    if ctx.message.author.id in admins:
        with open(dotenv_path, "r") as f:
            lines = f.readlines()
        with open(dotenv_path, "w") as f:
            for line in lines:
                try:
                    key, value = line.split('=')
                    if key == "ALLOWED_GUILDS":
                        value = '"' + value.replace('"', '') + f',{ctx.guild.id}"'
                    f.write(f'{key}={value}')
                except ValueError:
                    # syntax error
                    pass
        start()

bot.run(TOKEN)