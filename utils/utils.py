import discord
import utils.pnw_utils as pnw
import math

# A utility function to check whether or not a guild is a currently permitted guild
def check_guild(guild, allowed_guilds):
    if guild.id in allowed_guilds:
        return True
    else:
        return False

async def generic_tasks(LOG, ctx, allowed_guilds):
    if(not check_guild(ctx.guild, allowed_guilds)):
        # Write to the log that they attempted to use the command in the guild
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use the !{ctx.command} command in guild {ctx.guild.id}.\n')
        LOG.flush()
        # Let the user know they don't have permission to us it
        embed = discord.Embed(title="Current Server Not Permitted", description="You do not have permission to use commands in this server. Please contact an admin for support.", color=0xFF5733)
        await ctx.send(embed=embed)
        return False
    return True

def resource_tasks(nation_id):
    # Get the resource query result
    try:
        result = pnw.get_query("resource", nation_id)
    except Exception as inst:
        embed=discord.Embed(title=f"{inst.name}", description=f'{inst.message}', color=0xFF5733)
        return embed, True
    return result, False

# A utility function to initialize (or re-define) certain variables
def start(dotenv_path):
    # Initialize the variables to None in case they don't exist in the env file
    admins = []
    allowed_guilds = []
    # Open the env file
    with open(dotenv_path, "r") as f:
        # Loop through the lines and split them on the equals
        for line in f.readlines():
            key, value = line.strip().split("=")
            # If the key is ADMIN_IDS, then parse it
            if(key == "ADMIN_IDS"):  
                admins = [int(id) for id in value.split(",")]
            # If the key is ALLOWED_GUILDS, then parse it
            if(key == "ALLOWED_GUILDS"):
                allowed_guilds = [int(id) for id in value.split(",")]
    return admins, allowed_guilds

def col_round(x):
  frac = x - math.floor(x)
  if frac < 0.5: return math.floor(x)
  return math.ceil(x)