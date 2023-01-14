import discord
import utils.pnw_utils as pnw

COMMAND_ARGS = {
    "clearlog": "",
    "shutoff": "",
    "addserver": "(guild_id)",
    "restart": "",
    "pnwinfra": "start end (nation_id)",
    "pnwcity": "start end (nation_id)",
    "pnwfood": "nation_id",
    "pnwcoal": "nation_id",
    "pnwiron": "nation_id",
    "pnwoil": "nation_id"
}

# A utility function to check whether or not a guild is a currently permitted guild
def check_guild(guild, allowed_guilds):
    if guild.id in allowed_guilds:
        return True
    else:
        return False

def generic_tasks(LOG, ctx, allowed_guilds, args):
    if(not check_guild(ctx.guild, allowed_guilds)):
        # Write to the log that they attempted to use the command in the guild
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use the !{ctx.command} command in guild {ctx.guild.id}.\n')
        LOG.flush()
        # Let the user know they don't have permission to us it
        embed = discord.Embed(title="Current Server Not Permitted", description="You do not have permission to use commands in this server. Please contact an admin for support.", color=0xFF5733)
        return embed, True
    if len([x for x in (args) if x is None]) == len(args) or args[len(args) - 1] in ['-h', '-help', 'help']:
        embed=discord.Embed(title="Required Arguments", description=f"Arguments in parenthesis denote optional arguments.\n!{ctx.command} {COMMAND_ARGS[str(ctx.command)]}", color=0xFF5733)
        return embed, True
    if args[len(args) - 1] is not None:
        embed=discord.Embed(title="Invalid Arguments", description=f"Arguments in parenthesis denote optional arguments.\n!{ctx.command} {COMMAND_ARGS[str(ctx.command)]}", color=0xFF5733)
        return embed, True
    return None, False

def resource_tasks(nation_id):
    # Get the resource query result
    try:
        result = pnw.get_query("resource", nation_id)
    except Exception as inst:
        embed=discord.Embed(title=f"{inst.name}", description=f'{inst.message}', color=0xFF5733)
        return embed, True
    return result, False

# A utility function to message when the user is not an admin
async def non_admin(LOG, ctx):
    embed=discord.Embed(title="Improper Access", description=f'User {ctx.message.author} ({ctx.message.author.id}) does not have permissions to run this command. Contact an Admin to resolve this issue.', color=0xFF5733)
    LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to clear the logs, but did not have proper access.\n')
    LOG.flush()
    await ctx.send(embed=embed)

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