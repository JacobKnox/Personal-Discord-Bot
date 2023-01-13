import discord

# A utility function to check whether or not a guild is a currently permitted guild
def check_guild(guild, allowed_guilds):
    if guild.id in allowed_guilds:
        return True
    else:
        return False

# A utility function to check and handle an event where a message is not sent in a permitted guild
async def handle_guild(LOG, ctx, allowed_guilds):
    if(not check_guild(ctx.guild, allowed_guilds)):
        # Write to the log that they attempted to use the command in the guild
        LOG.write(f'{ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S")} {ctx.message.author} ({ctx.message.author.id}) attempted to use the !{ctx.command} command in guild {ctx.guild.id}.\n')
        LOG.flush()
        # Let the user know they don't have permission to us it
        embed = discord.Embed(title="Current Server Not Permitted", description="You do not have permission to use commands in this server. Please contact an admin for support.", color=0xFF5733)
        await ctx.send(embed=embed)
        return False
    return True

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