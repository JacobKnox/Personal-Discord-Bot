# Path related imports
from os.path import join, dirname
# Env related imports
from dotenv import load_dotenv
from os import getenv as ENV
# Other import modules
from pnwkit import *
import pnwkit  # PnW's Python API kit
import math  # Python's math library
# My imports
from utils.utils import *  # general utility functions
from exceptions import *  # custom exceptions

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# save my API key in a variable
API_KEY = ENV("PNW_API_KEY")
if not API_KEY or API_KEY == '':
    raise NoKeyException("PNW_API_KEY")
CONTINENT_RSS = {
    "af": ["oil", "bauxite", "uranium"],
    "an": ["oil", "coal", "uranium"],
    "as": ["oil", "iron", "uranium"],
    "au": ["coal", "bauxite", "lead"],
    "eu": ["coal", "iron", "lead"],
    "na": ["coal", "iron", "uranium"],
    "sa": ["oil", "bauxite", "lead"]
}
POWER_RSS = ["oil", "coal", "uranium"]
RSS = ["food", "coal", "oil", "iron", "lead", "bauxite",
       "uranium", "steel", "aluminum", "gasoline", "munitions"]
CITY_DISCOUNTS = {
    "UP": 50000000,
    "AUP": 100000000,
    "MP": 150000000
}

# create a QueryKit with my API key to create queries
kit = pnwkit.QueryKit(API_KEY)

### FUNCTIONS ###


# function for calculating the daily food revenue of a nation
# production accurate within a few ones or tens, usage accurate within a few thousands?
def calc_food_rev(api_result: pnwkit.Result) -> tuple[float, float, float]:
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
    month = radiation_result.game_info.game_date.month

    # intialize the food_usage variable with the usage from population
    food_usage = nation.population / 1000
    # merge the wars lists into one list
    wars = nation.defensive_wars + nation.offensive_wars
    if (sum([war.turns_left > 0 for war in wars]) > 0):
        # add the usage from soldiers in wartime
        food_usage += nation.soldiers / 500
    else:
        # add the usage from soldiers in peacetime
        food_usage += nation.soldiers / 750
    # initialize the food_production variable to 0
    food_production = 0
    # iterate over all cities in the nation
    for city in nation.cities:
        # initialize the city_production variable for that city to 0
        city_production = 0
        # set the production to the number of farms multiplied by the land divided by 500 (default production) minus 100 if they have Mass Irrigation
        city_production = city.farm * 12 * \
            (city.land / (500 - 100 * nation.massirr))
        # apply the production bonus
        city_production *= 1 + \
            max(my_round((city.farm - 1) * 0.0263157894737), 0)
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
        if (month > 5 and month < 9):
            season_affect = 1.2
        # winter
        elif (month > 11 or month < 3):
            season_affect = 0.8
    # if they're on South America, Africa, or Australia
    elif (continent in ["sa", "af", "au"]):
        # winter
        if (month > 5 and month < 9):
            season_affect = 0.8
        # summer
        elif (month > 11 or month < 3):
            season_affect = 1.2
    # if they're on Antarctica
    else:
        # Antarctica is unaffected by season, but gets a permanent -50% food production
        season_affect = 0.5
    # calculate the radiation factor on food production
    radiation_factor = max(
        1 - ((continent_radiation + radiation_result.game_info.radiation.global_) / 1000), nation.fallout_shelter * 0.1)
    # apply the seasonal and radiation factors to the total production
    food_production *= season_affect * radiation_factor
    # return the difference between the food_production and food_usage to determine net food revenue
    return my_round(food_production - food_usage), my_round(food_production), my_round(food_usage)


# function for calculating the cost of bringing a nation from their current city count to a goal
# completely accurate
def calc_city_cost(start_city: int, goal_city: int, nation_call: pnwkit.Result = None) -> float:
    # intialize a temporary total cost to 0
    total_cost = 0
    # intialize a temporary cost to 0
    city_cost = 0
    for city_num in range(start_city, goal_city):
        # calculate the cost of the next city
        city_cost = (50000 * ((city_num - 1) ** 3) + 150000 * city_num + 75000)
        # if the user has specified a nation
        if nation_call is not None:
            # if the nation has Metropolitan Planning project, apply it
            if (nation_call.nations[0].metropolitan_planning):
                city_cost -= (CITY_DISCOUNTS["MP"] +
                              CITY_DISCOUNTS["AUP"] + CITY_DISCOUNTS["UP"])
            # if the nation has Advanced Urban Planning project, apply it
            elif (nation_call.nations[0].advanced_urban_planning):
                city_cost -= (CITY_DISCOUNTS["AUP"] + CITY_DISCOUNTS["UP"])
            # if the nation has Urban Planning project, apply it
            elif (nation_call.nations[0].urban_planning):
                city_cost -= CITY_DISCOUNTS["UP"]
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
    return my_round(total_cost) if total_cost > 0 else 0


# function to calculate the cost of buying infra from a current amount to a goal amount
# accurate within a few tens or ones for multiples of 100, but within a few thousands for non-multiples of 100
def calc_infra_cost(current_infra: float, goal_infra: float, nation_call: pnwkit.Result = None) -> float:
    infra_cost = calculate_infrastructure_value(current_infra, goal_infra)
    if nation_call is not None:
        nation = nation_call.nations[0]
        if (infra_cost > 0):
            modifier = 1
            if (nation.advanced_engineering_corps):
                modifier -= 0.1
            elif (nation.center_for_civil_engineering):
                modifier -= 0.05
            if (nation.domestic_policy == pnwkit.data.DomesticPolicy(5) and nation.government_support_agency):
                modifier -= 0.075
            elif (nation.domestic_policy == pnwkit.data.DomesticPolicy(5)):
                modifier -= 0.05
            infra_cost *= modifier
    return my_round(infra_cost)


def calc_land_cost(current_land: float, goal_land: float, nation_call: pnwkit.Result = None) -> float:
    land_cost = calculate_land_value(current_land, goal_land)
    if nation_call is not None:
        nation = nation_call.nations[0]
        if (land_cost > 0):
            modifier = 1
            if (nation.advanced_engineering_corps):
                modifier -= 0.1
            elif (nation.arable_land_agency):
                modifier -= 0.05
            if (nation.domestic_policy == pnwkit.data.DomesticPolicy(6) and nation.government_support_agency):
                modifier -= 0.075
            elif (nation.domestic_policy == pnwkit.data.DomesticPolicy(6)):
                modifier -= 0.05
            land_cost *= modifier
    return my_round(land_cost)


def calc_raw_rev(nation_call: pnwkit.Result, resource: str) -> tuple[float, float, float]:
    nation = nation_call.nations[0]
    # initialize helper variables for production and usage to 0
    production = 0
    mill_usage = 0
    power_usage = 0
    nation_info = {
        'oil': [nation.emergency_gasoline_reserve, 3, 1],
        'coal': [nation.iron_works, 3, 0.36],
        'iron': [nation.iron_works, 3, 0.36],
        'bauxite': [nation.bauxite_works, 3, 0.36],
        'lead': [nation.arms_stockpile, 6, 0.34],
        'uranium': [nation.uranium_enrichment_program, 0, 0]
    }
    if (resource not in nation_info.keys()):
        raise InvalidResourceException(resource)
    project = nation_info[resource][0]
    manu_used = nation_info[resource][1]
    project_mod = nation_info[resource][2]
    if (nation.resource_production_center and resource in CONTINENT_RSS[nation.continent] and len(nation.cities) < 16):
        production += (math.ceil(min(len(nation.cities), 10) / 2)) * 12
    # loop over each city in the nation
    for city in nation.cities:
        # calculate its oil production
        info = {
            'oil': [city.oil_well, city.gasrefinery, city.oil_power],
            'coal': [city.coal_mine, city.steel_mill, city.coal_power],
            'iron': [city.iron_mine, city.steel_mill, 0],
            'bauxite': [city.bauxite_mine, city.aluminum_refinery, 0],
            'lead': [city.lead_mine, city.munitions_factory, 0],
            'uranium': [city.uranium_mine, 0, city.nuclear_power]
        }
        # number of the improvement (mine/well) in the city
        raw_improvement = info[resource][0]
        # number of the improvement (mill/refinery/factory) in the city
        manu_improvement = info[resource][1]
        # number of power plants in the city
        power = info[resource][2]
        city_production = raw_improvement * 3
        if (resource == 'uranium'):
            city_production *= (1 + project) * (1 +
                                                max(my_round((raw_improvement - 1) * 0.125), 0))
        else:
            city_production *= (1 +
                                max(my_round((raw_improvement - 1) * 0.05555555555), 0))
        production += city_production
        city_mill = manu_improvement * manu_used
        city_mill *= (1 + max(my_round((manu_improvement - 1) *
                      0.125), 0)) * (1 + project * project_mod)
        mill_usage += city_mill
        if (resource == 'uranium'):
            power_infra = 2000
            infra_per = 1000
        else:
            power_infra = 500
            infra_per = 100
        if (resource in POWER_RSS and city.powered and power > 0):
            temp_infra = city.infrastructure
            for _ in range(0, power):
                if (temp_infra >= power_infra):
                    power_usage += (power_infra / infra_per) * 1.2
                    temp_infra -= power_infra
                elif (temp_infra > 0):
                    power_usage += math.ceil(temp_infra / infra_per) * 1.2
                    temp_infra = 0
    return my_round(production - mill_usage - power_usage), my_round(production), my_round(mill_usage + power_usage)


def calc_manu_rev(nation_call: pnwkit.Result, resource: str) -> float:
    nation = nation_call.nations[0]
    production = 0
    nation_info = {
        'steel': [nation.iron_works, 9, 0.36],
        'aluminum': [nation.bauxite_works, 9, 0.36],
        'gasoline': [nation.emergency_gasoline_reserve, 6, 2, 0.34],
        'munitions': [nation.arms_stockpile, 18, 1]
    }
    if (resource not in nation_info.keys()):
        raise InvalidResourceException(resource)
    project = nation_info[resource][0]
    generated = nation_info[resource][1]
    project_mod = nation_info[resource][2]
    for city in nation.cities:
        city_info = {
            'steel': city.steel_mill,
            'aluminum': city.aluminum_refinery,
            'gasoline': city.gasrefinery,
            'munitions': city.munitions_factory
        }
        if city.powered:
            improvement = city_info[resource]
            production += improvement * generated * \
                (1 + max(my_round((improvement - 1) * 0.125), 0)) * \
                (1 + project * project_mod)
    return my_round(production)


def market_info(resource: str) -> tuple[int, int]:
    if resource not in RSS:
        raise InvalidResourceException(resource)
    return get_query(query_type="market", resource=resource, buy_or_sell="buy").trades[0].price, get_query(query_type="market", resource=resource, buy_or_sell="sell").trades[0].price


### The following code is modified code from the open source Rift project ###
### (https://github.com/mrvillage/rift/blob/master/bot/src/funcs/tools.py) ###
def infrastructure_price(amount: float, /) -> float:
    return ((abs(amount - 10) ** 2.2) / 710) + 300


def calculate_infrastructure_value(start: float, end: float, /) -> float:
    start = my_round(start)
    end = my_round(end)
    difference = end - start
    chunk = my_round(infrastructure_price(start)) if difference >= 0 else 150
    if difference > 100 and difference % 100 == 0:
        return chunk * 100 + calculate_infrastructure_value(start + 100, end)
    if difference > 100 and difference % 100 != 0:
        return chunk * (difference % 100) + calculate_infrastructure_value(start + difference % 100, end)
    return chunk * difference


def land_price(amount: float, /) -> float:
    return (0.002 * (amount - 20) * (amount - 20)) + 50


def calculate_land_value(start: float, end: float) -> float:
    start = my_round(start)
    end = my_round(end)
    difference = end - start
    chunk = 50 if difference < 0 else my_round(land_price(start))
    if difference > 500 and difference % 500 == 0:
        return chunk * 500 + calculate_land_value(start + 500, end)
    if difference > 500 and difference % 500 != 0:
        return chunk * (difference % 500) + calculate_land_value(start + difference % 500, end)
    return chunk * difference
### End of code from Rift ###


def get_query(query_type: str = "general", nation_id: int = None, api_key: str = API_KEY, resource: str = None, buy_or_sell: str = None) -> pnwkit.Result:
    if query_type == "food":
        query = kit.query(
            "nations", {
                "id": nation_id,
                "first": 1,
            },
            """
            cities{
                farm
                land
            }
            defensive_wars{
                turns_left
            }
            offensive_wars{
                turns_left
            }
            soldiers
            nation_name
            population
            continent
            resource_production_center
            massirr
            fallout_shelter
            """)
    elif query_type == "market":
        query = kit.query(
            "trades", {
                "offer_resource": resource,
                "buy_or_sell": buy_or_sell,
                "accepted": False,
                "type": pnwkit.TradeType.GLOBAL,
                "orderBy": pnwkit.OrderBy("return_amount", pnwkit.Order.ASC if buy_or_sell == "sell" else pnwkit.Order.DESC)
            },
            """
            price
            """
        )
    elif query_type == "city":
        query = kit.query(
            "nations", {
                "id": nation_id,
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
    elif query_type == "infraland":
        query = kit.query(
            "nations", {
                "id": nation_id,
                "first": 1
            },
            """
                domestic_policy
                nation_name
                government_support_agency
                center_for_civil_engineering
                advanced_engineering_corps
                arable_land_agency
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
    elif query_type == "resource":
        query = kit.query(
            "nations", {
                "id": nation_id,
                "first": 1,
            },
            """
            cities{
                coal_mine
                iron_mine
                steel_mill
                powered
                coal_power
                infrastructure
                oil_well
                oil_power
                gasrefinery
                munitions_factory
                lead_mine
                aluminum_refinery
                bauxite_mine
                nuclear_power
                uranium_mine
            }
            nation_name
            continent
            resource_production_center
            iron_works
            arms_stockpile
            emergency_gasoline_reserve
            bauxite_works
            uranium_enrichment_program
            """)
    elif query_type == "treasure":
        query = kit.query("treasures", {}, """
                name,
                color,
                continent,
                bonus,
                spawn_date,
                nation_id,
                nation
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
    else:
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
    try:
        result = query.get()
        if query_type not in ["radiation", "treasure", "market"] and len(result.nations) == 0:
            raise NoNationFoundException(
                "No nation exists with that nation id.")
        return result
    except NoNationFoundException as inst:
        raise inst
    # except Exception as inst:
    #    raise GeneralException(inst)


# "Test" API call to get a bunch of information
general_query = get_query(nation_id=244934)
