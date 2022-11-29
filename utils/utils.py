# A utility function to check whether or not a guild is a currently permitted guild
def check_guild(guild, allowed_guilds):
    if guild.id in allowed_guilds:
        return True
    else:
        return False

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