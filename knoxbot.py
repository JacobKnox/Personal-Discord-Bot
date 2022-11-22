from os import getenv as ENV
from os.path import join, dirname
import discord
from dotenv import load_dotenv
from discord.ext import commands
from pnw_utils import *

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TOKEN = ENV("DISCORD_TOKEN")
GUILD = ENV('DISCORD_GUILD')
API_KEY = ENV("API_KEY")
LOG = open("commands_log.log", "a")
ADMINS = [int(id) for id in ENV("ADMIN_IDS").split(",")]

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )
    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')
        
# Add a command to calculate the cost of infrastructure
@bot.command(name='infra')
async def calc_infra(ctx, *args):
    # If there are less than two arguments, then it isn't a valid command call
    if len(args) < 2 or len(args) > 3:
        embed=discord.Embed(title="Invalid Arguments", description="This function requires two or three arguments:\n!infra [nation id] [start] [end]\n!infra [start] [end]")
    # If there are two arguments, then just calculate the difference between the two
    elif len(args) == 2:
        infra_cost = calculate_infrastructure_value(float(args[0]), float(args[1]))
        embed=discord.Embed(title="Calculate Infrastructure", description=f'The cost to go from {args[0]} to {args[1]} is:\n${infra_cost: ,.2f}', color=0xFF5733)
    # If there are three arguments, then calculate the difference between the two considering their nation
    elif len(args) == 3:
        # Assemble the query with their nation ID
        result = get_query("infra", args[0])
        infra_cost = calc_infra_cost(result, float(args[1]), float(args[2]))
        embed=discord.Embed(title="Calculate Infrastructure", description=f'The cost to go from {args[1]: ,.2f} to {args[2]: ,.2f} for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={args[0]}) is:\n${infra_cost: ,.2f}', color=0xFF5733)
    await ctx.send(embed=embed)
    
@bot.command(name='city')
async def calc_city(ctx, nation_id, end):
    result = get_query("city", nation_id)
    city_cost = calc_city_cost(result, int(end))
    await ctx.send(f'${city_cost: ,.2f}')

@bot.command(name="food")
async def calc_food(ctx, nation_id):
    result = get_query("food", nation_id)
    net_food, food_production, food_usage = calc_food_rev(result)
    embed=discord.Embed(title="Food Statistics", description=f'Statistics about food revenue for [{result.nations[0].nation_name}](https://politicsandwar.com/nation/id={nation_id}):\nProduction: {abs(food_production): ,.2f}\nUsage: {food_usage: ,.2f}\nNet: {net_food: ,.2f}', color=0xFF5733)
    LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) used the !food command with id {nation_id}.\n')
    LOG.flush()
    await ctx.send(embed=embed)

@bot.command(name="clearlog")
async def clear_log(ctx):
    if ctx.message.author.id in ADMINS:
        with open("commands_log.log",'w') as _:
            pass
        embed=discord.Embed(title="Log Clear", description=f'Admin {ctx.message.author} ({ctx.message.author.id}) has cleared the logs.', color=0xFF5733)
    else:
        embed=discord.Embed(title="Improper Access", description=f'User {ctx.message.author} ({ctx.message.author.id}) does not have permissions to run this command. Contact an Admin to resolve this issue.', color=0xFF5733)
    await ctx.send(embed=embed)

bot.run(TOKEN)