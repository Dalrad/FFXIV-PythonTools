import requests

# Usage: Change item_name to in game matching item name
# Run script, it will return a place to find item cheapest
# TODO [ ] - Make CLI Friendly

# TODO [ ] - Add function to check cheapest route for all subcrafts
# TODO [ ] - Then - Add support for disabling certain subcrafts

# TODO [ ] - Convert to use UI python library / or serve as an API for a React Site
"""
{
    ...item_info
    quantity: int
    ingredient_0-7_info
    listings: {
        "world_name": {
            world_name
            raw_price
            ingredient_0-7_price
            total_price: 
        }
    }
    ingredient_0-7_info
}
"""


def function_to_insert_prices(item, universalis_data):
    listing_dict = {}
    expectedIngredients = -1
    for i in range(6):
        if item.get(f"ingredient_{i}_info"):
            expectedIngredients += 1

    for i in range(6):
        ingredient_info_key = f"ingredient_{i}_info"
        ingredient_price_key = f"ingredient_{i}_price"

        ingredient_info = item.get(ingredient_info_key)
        if not ingredient_info:
            continue

        item_id = str(ingredient_info.get("item_id"))
        if item_id not in universalis_data.get("items", {}):
            print("Item not found")
            continue

        # Get the listings for the item_id
        listings = universalis_data["items"].get(item_id).get("listings")

        for listing in listings:
            world_name = listing.get("worldName")
            listing_total = listing.get("total")
            listing_quantity = listing.get("quantity")

            # Check if the listing meets the quantity requirement
            if listing_quantity < ingredient_info.get("quantity", 0):
                continue

            # Initialize or update the world entry in listing_dict
            world_info = listing_dict.setdefault(world_name, {"all_ingredients": False})
            current_price = world_info.get(ingredient_price_key, float("inf"))

            if listing_total < current_price:
                # We will always have a lowest price so we can avoid running this as often
                if i == expectedIngredients:
                    world_info["all_ingredients"] = True
                world_info["world_name"] = world_name
                world_info[ingredient_price_key] = listing_total

        # Process the child item
        item[ingredient_info_key] = function_to_insert_prices(
            ingredient_info, universalis_data
        )

    base_item_price_dict = {}
    base_listings = universalis_data.get("items", {}).get(item.get("id", 0), [])

    for listing in base_listings:
        world_name = listing.get("worldName")
        total_price = listing.get("total")

        if world_name not in base_item_price_dict or total_price < base_item_price_dict[
            world_name
        ].get("total", 999999999):
            base_item_price_dict[world_name] = {"total": total_price}

    item["listings"] = listing_dict
    item["base_item_price_dict"] = base_item_price_dict
    return item


def call_item_search_api(item):
    url = "https://xivapi.com/search?string=" + item
    headers = {"User-Agent": "&lt;User-Agent&gt;"}
    body = {"indexes": "Recipe"}

    try:
        response = requests.get(url, headers=headers, json=body)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
            return None
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None


def callRecipeAPI(item_id):
    url = "https://xivapi.com/recipe/" + str(item_id)
    headers = {"User-Agent": "&lt;User-Agent&gt;"}

    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
            return None
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None


def item_recipe_builder(itemName):
    results = call_item_search_api(itemName)
    if len(results.get("Results")) == 0:
        print("This item had no results")
        return None

    if "Url" not in results.get("Results")[0]:
        print("This recipe had a missing URL")
        return None

    return build_shopping_cart_item(results.get("Results", [])[0].get("ID"))


def build_shopping_cart_item(recipe_id):
    recipe_api_result = callRecipeAPI(recipe_id)

    base_item = {
        "item_id": recipe_api_result.get("ItemResult").get("ID"),
        "recipe_id": recipe_id,
        "name": recipe_api_result.get("Name_en"),
        "quantity": 1,
        "listings": {},
        "base_price_of_item": [],
    }

    for item_number in range(8):
        if recipe_api_result.get(f"AmountIngredient{item_number}", 0) != 0:
            # If the item has a recipe
            ingredient_recipe_prop = f"ItemIngredientRecipe{item_number}"
            ingredient_info_prop = f"ingredient_{item_number}_info"

            if recipe_api_result.get(ingredient_recipe_prop) is not None:
                base_item[ingredient_info_prop] = build_shopping_cart_item(
                    recipe_api_result.get(ingredient_recipe_prop)[0].get("ID")
                )

                base_item[ingredient_info_prop]["quantity"] = recipe_api_result.get(
                    f"AmountIngredient{item_number}"
                )
            # If the item has no corresponding attached recipe, just insert details off its details from the recipe it's in
            else:
                base_item[ingredient_info_prop] = {
                    "item_id": recipe_api_result.get(
                        f"ItemIngredient{item_number}"
                    ).get("ID"),
                    "recipe_id": None,
                    "name": recipe_api_result.get(f"ItemIngredient{item_number}").get(
                        "Name_en"
                    ),
                    "quantity": recipe_api_result.get(f"AmountIngredient{item_number}"),
                    "listings": {},
                    "base_price_of_item": [],
                }

    return base_item


def call_current_price_universalis(item_recipe_array):
    item_recipe_array_formatted = ",".join(map(str, item_recipe_array))
    url = "https://universalis.app/api/v2/North-America/" + item_recipe_array_formatted
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
            return None
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None


def recursive_item_id_array(recipeDict, recipeIdArray=[]):
    recipeIdArray.append(recipeDict.get("item_id"))

    for i in range(8):
        if recipeDict.get(f"ingredient_{i}_info"):
            recursive_item_id_array(
                recipeDict.get(f"ingredient_{i}_info"), recipeIdArray
            )

    return list(set(recipeIdArray))


def build_enabled_world():
    worlds_toggling = {
        "aether_servers": {
            "full_disabled": False,
            "Adamantoise": True,
            "Cactuar": True,
            "Faerie": True,
            "Gilgamesh": True,
            "Jenova": True,
            "Midgardsormr": True,
            "Sargatanas": True,
            "Siren": True,
        },
        "crystal_servers": {
            "full_disabled": False,
            "Balmung": True,
            "Brynhildr": True,
            "Coeurl": True,
            "Diabolos": True,
            "Goblin": True,
            "Malboro": True,
            "Mateus": True,
            "Zalera": True,
        },
        "dynamis_servers": {
            "full_disabled": False,
            "Cuchulainn": True,
            "Golem": True,
            "Halicarnassus": True,
            "Kraken": True,
            "Maduin": True,
            "Marilith": True,
            "Rafflesia": True,
            "Seraph": True,
        },
        "primal_servers": {
            "full_disabled": False,
            "Behemoth": True,
            "Excalibur": True,
            "Exodus": True,
            "Famfrit": True,
            "Hyperion": True,
            "Lamia": True,
            "Leviathan": True,
            "Ultros": True,
        },
    }

    enabled_world_dict = {}
    for server_name, world_group in worlds_toggling.items():
        for world_name, world_setting in world_group.items():
            enabled_world_dict[world_name] = world_setting

            if world_group.get("full_disabled") is True:
                enabled_world_dict[world_name] = False

    return enabled_world_dict


def cheapest_from_subcrafts(price_included_recipe_list):
    cheapest_world = None
    enabled_world_status = build_enabled_world()
    for world_name, listing in price_included_recipe_list.get("listings").items():
        if enabled_world_status.get(world_name, False):
            # range excludes crystals
            price = 0
            for i in range(6):
                price += listing.get(f"ingredient_{i}_price", 0)

            if not cheapest_world or cheapest_world.get("price") > price:
                cheapest_world = listing
                cheapest_world["price"] = price

    return cheapest_world


item_name = "Archeo Kingdom Coat of Healing"

shopping_list = item_recipe_builder(item_name)
item_ids_from_list = recursive_item_id_array(shopping_list)
universalis_returns = call_current_price_universalis(item_ids_from_list)
price_attached = function_to_insert_prices(shopping_list, universalis_returns)
cheapest_world = cheapest_from_subcrafts(price_attached)


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


print("\n\n")
print(
    f"Looking for {bcolors.OKCYAN}{bcolors.UNDERLINE}{item_name}{bcolors.ENDC}{bcolors.ENDC}"
)
print(
    f"{bcolors.OKGREEN}{cheapest_world.get('world_name')}{bcolors.ENDC} has all sub-items for price of [ {bcolors.OKGREEN}{cheapest_world.get('price')}{bcolors.ENDC} ] gil"
)
print("\n\n")
