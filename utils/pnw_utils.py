# Path related imports
from os.path import join, dirname
# Env related imports
from dotenv import load_dotenv
from os import getenv as ENV
# Other import modules
import pnwkit # PnW's Python API kit
import math # Python's math library

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# save my API key in a variable
API_KEY = ENV("PNW_API_KEY")
RESOURCES  = {
    "af": ["oil", "bauxite", "uranium"],
    "an": ["oil", "coal", "uranium"],
    "as": ["oil", "iron", "uranium"],
    "au": ["coal", "bauxite", "lead"],
    "eu": ["coal", "iron", "lead"],
    "na": ["coal", "iron", "uranium"],
    "sa": ["oil", "bauxite", "lead"]
}

# create a QueryKit with my API key to create queries
kit = pnwkit.QueryKit(API_KEY)

### FUNCTIONS ###


# function for calculating the daily food revenue of a nation
# production accurate within a few ones or tens, usage accurate within a few thousands?
def calc_food_rev(api_result):
    nation = api_result.nations[0]
    # querying radiation information from GameInfo
    radiation_result = get_query("radiation")
    RADIATION = {
        "af": radiation_result.game_info.radiation.africa,
        "an": radiation_result.game_info.radiation.antarctica,
        "as": radiation_result.game_info.radiation.asia,
        "au": radiation_result.game_info.radiation.australia,
        "eu": radiation_result.game_info.radiation.europe,
        "na": radiation_result.game_info.radiation.north_america,
        "sa": radiation_result.game_info.radiation.south_america
    }
    
    # intialize the food_usage variable with the usage from population
    food_usage = nation.population / 1000
    # if the nation is in any wars
    if (len(nation.defensive_wars) > 0 or len(nation.offensive_wars) > 0):
        # add the usage from soldiers in wartime
        food_usage += nation.soldiers / 500
    else:
        # add the usage from soldiers in peacetime
        food_usage += nation.soldiers / 750
    # initialize the food_production variable to 0
    food_production = 0
    if(nation.resource_production_center and len(nation.cities) < 16):
        food_production += (1 + math.floor(min(len(nation.cities), 10) / 2)) * 12
    # iterate over all cities in the nation
    for city in nation.cities:
        # initialize the city_production variable for that city to 0
        city_production = 0
        # if the nation has the Mass Irrigation national project
        if (nation.massirr):
            # set the production to the number of farms multiplied by the land divided by 400 (effect of Mass Irrigation)
            city_production = city.farm * 12 * (city.land / 400)
        else:
            # set the production to the number of farms multiplied by the land divided by 500 (default production)
            city_production = city.farm * 12 * (city.land / 500)
        # if the nation has more than one farm
        if (city.farm > 1):
            # apply the production bonus
            city_production *= 1 + (city.farm - 1) * 0.0263157894737
        # add the current city's production to the nation's total production
        food_production += city_production
    # the seasonal affect on food production (need to check what continent and season the nation is on)
    season_affect = 1
    # save the continent into a variable
    continent = nation.continent
    continent_radiation = RADIATION[continent]
    # if they're on North America, Europe, or Asia
    if (continent in ["na", "eu", "as"]):
        # summer
        if (radiation_result.game_info.game_date.month > 5 and radiation_result.game_info.game_date.month < 9):
            season_affect = 1.2
        # winter
        else:
            season_affect = 0.8
    # if they're on South America, Africa, or Australia
    elif (continent in ["sa", "af", "au"]):
        # winter
        if (radiation_result.game_info.game_date.month > 5 and radiation_result.game_info.game_date.month < 9):
            season_affect = 0.8
        # summer
        else:
            season_affect = 1.2
    # if they're on Antarctica
    else:
        # Antarctica is unaffected by season, but gets a permanent -50% food production
        season_affect = 0.5
    # calculate the radiation factor on food production
    radiationFactor = 1 - ((continent_radiation + radiation_result.game_info.radiation.global_) / 1000)
    # apply the seasonal factor to the total production
    food_production *= season_affect
    # apply the radiation factor to the total production
    food_production *= radiationFactor
    # return the difference between the food_production and food_usage to determine net food revenue
    return round(food_production - food_usage, 2), food_production, food_usage


# function for calculating the cost of bringing a nation from their current city count to a goal
# completely accurate
def calc_city_cost(start_city, goal_city, nation_call = None):
    # intialize a temporary total cost to 0
    total_cost = 0
    # intialize a temporary cost to 0
    city_cost = 0
    for city_num in range(start_city, goal_city):
        # calculate the cost of the next city
        city_cost = (50000 * pow((city_num - 1), 3) + 150000 * city_num + 75000)
        # if the user has specified a nation
        if nation_call is not None:
            # if the nation has Urban Planning project, apply it
            if (nation_call.nations[0].urban_planning):
                city_cost -= 50000000
            # if the nation has Advanced Urban Planning project, apply it
            if (nation_call.nations[0].advanced_urban_planning):
                city_cost -= 100000000
                # if the nation has Metropolitan Planning project, apply it
            if (nation_call.nations[0].metropolitan_planning):
                city_cost -= 150000000
            # if the nation's domestic policy is currently Manifest Destiny, apply it
            if (nation_call.nations[0].domestic_policy == pnwkit.data.DomesticPolicy(1)):
                # if the nation has Government Support Agency project, then couple its effects with Manifest Destiny
                if (nation_call.nations[0].government_support_agency):
                    city_cost *= 0.925
                # otherwise, just apply Manifest Destiny
                else:
                    city_cost *= 0.95
        # add the cost of the next city to the total cost
        total_cost += city_cost
    # finally, return the total city cost
    return total_cost if total_cost > 0 else 0


# function to calculate the cost of buying infra from a current amount to a goal amount
# accurate within a few tens or ones for multiples of 100, but within a few thousands for non-multiples of 100
def calc_infra_cost(current_infra, goal_infra, nation_call = None):
    infra_cost = calculate_infrastructure_value(current_infra, goal_infra)
    if nation_call is not None:
        nation = nation_call.nations[0]
        if (infra_cost > 0):
            modifier = 1
            if(nation.center_for_civil_engineering):
                modifier -= 0.05
                if(nation.advanced_engineering_corps):
                    modifier -= 0.05
            if (nation.domestic_policy == pnwkit.data.DomesticPolicy(5) and nation.government_support_agency):
                modifier -= 0.075
            elif (nation.domestic_policy == pnwkit.data.DomesticPolicy(5)):
                modifier -= 0.05
            infra_cost *= modifier
    return round(infra_cost, 2)


def calc_coal_rev(nation_call):
    nation = nation_call.nations[0]
    # initialize helper variables for production and usage to 0
    coal_production = 0
    mill_usage = 0
    power_usage = 0
    if(nation.resource_production_center and "coal" in RESOURCES[nation.continent] and len(nation.cities) < 16):
        coal_production += (1 + math.floor(min(len(nation.cities), 10) / 2)) * 12
    # loop over each city in the nation
    for city in nation.cities:
        # calculate its coal production
        city_coal = city.coal_mine * 3
        city_coal *= (1 + ((city.coal_mine - 1) * 0.055555555555))
        coal_production += city_coal
        city_mill = city.steel_mill * 3
        city_mill *= (1 + ((city.steel_mill - 1) * 0.125))
        if (nation.iron_works):
            city_mill *= 1.36
        mill_usage += city_mill
        if (city.powered and city.coal_power > 0):
            temp_infra = city.infrastructure
            for _ in range(0, city.coal_power):
                if (temp_infra >= 500):
                    power_usage += 6
                    temp_infra -= 500
                elif (temp_infra > 0):
                    power_usage += (math.ceil(temp_infra) / 100) * 1.2
                    temp_infra = 0
    return round(coal_production - mill_usage - power_usage, 2), coal_production, (mill_usage + power_usage)


### The following code is taken directly from the open source Rift project ###
### (https://github.com/mrvillage/rift/blob/master/bot/src/funcs/tools.py) ###
def infrastructure_price(amount: float, /) -> float:
    return ((abs(amount - 10) ** 2.2) / 710) + 300


def calculate_infrastructure_value(start: float, end: float, /) -> float:
    value = 0
    start = round(start, 2)
    end = round(end, 2)
    difference = end - start
    if not difference:
        return 0
    if difference < 0:
        return 150 * difference
    if difference > 100 and difference % 100 == 0:
        chunk = round(infrastructure_price(start), 2) * 100
        return value + chunk + calculate_infrastructure_value(start + 100, end)
    if difference > 100 and difference % 100 != 0:
        chunk = round(infrastructure_price(start), 2) * (difference % 100)
        return (
            value
            + chunk
            + calculate_infrastructure_value(start + difference % 100, end)
        )
    if difference <= 100:
        chunk = round(infrastructure_price(start), 2) * difference
        return value + chunk
    return value


### End of code from Rift ###

def get_query(query_type = "general", nation_id = None, api_key = API_KEY):
    if query_type == "food":
        query = kit.query(
            "nations", {
                "id": int(nation_id),
                "first": 1,
            },
            """
            cities{
                farm
                land
            }
            defensive_wars{
            }
            offensive_wars{
            }
            soldiers
            nation_name
            population
            continent
            resource_production_center
            massirr
            """)
    elif query_type == "city":
        query = kit.query(
            "nations", {
                "id": int(nation_id),
                "first": 1
            },
            """
            cities{
            }
            advanced_urban_planning
            metropolitan_planning
            nation_name
            urban_planning
            domestic_policy
            government_support_agency
            """)
    elif query_type == "infra":
        query = kit.query(
                "nations", {
                    "id": int(nation_id),
                    "first": 1
                },
                """
                domestic_policy
                nation_name
                government_support_agency
                center_for_civil_engineering
                advanced_engineering_corps
                """)
    elif query_type == "radiation":
        query = kit.query(
            "game_info", {}, """
            game_date
            radiation {
                africa
                antarctica
                asia
                australia
                europe
                global
                north_america
                south_america
            }
            """)
    elif query_type == "coal":
        query = kit.query(
            "nations", {
                "id": int(nation_id),
                "first": 1,
            },
            """
            cities{
                coal_mine
                steel_mill
                powered
                coal_power
                infrastructure
            }
            nation_name
            continent
            resource_production_center
            iron_works
            """)
    elif query_type == "general":
        query = kit.query(
                "nations", {
                    "id": nation_id,
                    "first": 1
                }, """
                population
                soldiers
                continent
                defensive_wars{
                    turns_left
                }
                offensive_wars{
                    turns_left
                }
                cities{
                    farm
                    land
                    coal_mine
                    steel_mill
                    powered
                    infrastructure
                    coal_power
                }
                massirr
                advanced_urban_planning
                urban_planning
                domestic_policy
                government_support_agency
                center_for_civil_engineering
                advanced_engineering_corps
                iron_works
                resource_production_center
                """)
    elif query_type == "my_info":
        if api_key == API_KEY:
            query = kit.query(
                    "nations", {
                        "id": nation_id,
                        "first": 1
                    }, """
                    soldiers
                    tanks
                    aircraft
                    ships
                    """)
        else:
            temp_kit = pnwkit.QueryKit(api_key)
            query = temp_kit.query(
                    "nations", {
                        "id": nation_id,
                        "first": 1
                    }, """
                    soldiers
                    tanks
                    aircraft
                    ships
                    """)
    return query.get()
        
# "Test" API call to get a bunch of information
general_query = get_query(nation_id = 244934)