import requests
import json 
import time

# --- Database Schema Key ---
# We define a list to store all the collected Pokémon data
pokemon_data_list = []

def call_pokemon_api(pokemon_id):
    """
    Makes a GET request to the core PokéAPI endpoint for a specific Pokémon ID.
    (https://pokeapi.co/api/v2/pokemon/{id})
    """
    base_url = "https://pokeapi.co/api/v2/pokemon/"
    url = f"{base_url}{pokemon_id}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    except requests.exceptions.RequestException:
        return None

def call_pokemon_species_api(pokemon_id):
    """
    Makes a GET request to the Pokémon Species endpoint to get Egg Group data.
    (https://pokeapi.co/api/v2/pokemon-species/{id})
    """
    base_url = "https://pokeapi.co/api/v2/pokemon-species/" 
    url = f"{base_url}{pokemon_id}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    except requests.exceptions.RequestException:
        return None


def call_evolution_chain_api (chain_url):
    if not chain_url:
        return None
    
    try:
        response = requests.get(chain_url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    except requests.exceptions.RequestException:
        return None
    

def call_pokemon_location_api (pokemon_id):
    base_url = "https://pokeapi.co/api/v2/pokemon/"
    url = f"{base_url}{pokemon_id}/encounters"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
        
    except requests.exceptions.RequestException:
        return None

def evolution_api (pokemon_id):
    base_url = "https://pokeapi.co/api/v2/evolution-chain/"
    url = f"{base_url}{pokemon_id}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    except requests.exceptions.RequestException:
        return None

    
def generation_name_parser (species_data):
    generation_dict = species_data.get('generation')
    generation_name = generation_dict.get('name').replace('generation-', '')

    match generation_name:
        case 'i': result = 1
        case 'ii': result = 2
        case 'iii': result = 3
        case 'iv': result = 4
        case 'v': result = 5
        case 'vi': result = 6
        case 'vii': result = 7
        case 'viii': result = 8
        case 'ix': result = 9

    return result

# Mega evolutions might be a pain, because I am not sure if all mega's have mega in the name
def mega_evolution_check(species_data):
    if 'varieties' in species_data:
        for variety in species_data['varieties']:
            if not variety['is_default']:
                variety_name = variety['pokemon']['name']
                if 'mega' in variety_name:
                    return True
    return False

def region_finder (species_data):
    generation_url = species_data.get('generation', {}).get('url')
    
    if generation_url:
        try:
            gen_response = requests.get(generation_url)
            if gen_response.status_code == 200:
                gen_data = gen_response.json()
                # Extract the region name
                region_name = gen_data.get('main_region', {}).get('name', 'Unknown').capitalize()
            else:
                region_name = 'API Error'
        except requests.exceptions.RequestException:
            region_name = 'Network Error'
    else:
        region_name = 'N/A'

    return region_name

def get_evolution_stone(evolution_chain_data, target_pokemon_name):
    """
    Traverses the evolution chain to find the specific stone required for the target Pokémon.
    Returns: evolution_stone: str | None
    """

    evolution_stone = None
    
    if not evolution_chain_data or 'chain' not in evolution_chain_data:
        return None

    # Helper function to recursively search the evolution chain
    def find_details(chain_link, target_name):
        nonlocal evolution_stone
        
        for evolves_to_link in chain_link.get('evolves_to', []):
            evolved_species = evolves_to_link['species']['name'].capitalize()
            
            if evolved_species == target_name:
                details = evolves_to_link['evolution_details'][0] 
                
                evolution_details = evolves_to_link.get('evolution_details', [])

                if not evolution_details:
                    return 
                    
                details = evolution_details[0]

                trigger = details.get('trigger', {}).get('name')
                
                # Check for stone evolution logic
                if trigger == 'use-item':
                    item_name = details.get('item', {}).get('name')
                    if item_name:
                        # Format the stone name (e.g., 'thunder-stone' -> 'Thunder Stone')
                        evolution_stone = item_name.replace('-', ' ').title()
                
                return # Stop the search once the stone is found
            
            # Recurse down the chain
            find_details(evolves_to_link, target_name)
                
    # Start the search from the base of the chain
    find_details(evolution_chain_data['chain'], target_pokemon_name)
    
    if (evolution_stone is not None):
        return True
    else:
        return False 

def is_fossile (pokemon_id):
    fossile_id_list = [138,139,140,141,142,345,346,347,348,408,409,410,411,564,565,566,567,696,697,698,699,880,881,882,883]
    return pokemon_id in fossile_id_list   
def is_starter (pokemon_id):
    starter = False
    # Kanto Starters
    if (1 <= pokemon_id <= 9):
        starter = True
    elif (152 <= pokemon_id <= 160):
        starter = True
    elif (252 <= pokemon_id <= 260):
        starter = True
    elif (387 <= pokemon_id <= 395):
        starter = True
    elif (495 <= pokemon_id <= 503):
        starter = True
    elif (650 <= pokemon_id <= 658):
        starter = True
    elif (722 <= pokemon_id <= 730):
        starter = True
    elif (810 <= pokemon_id <= 818):
        starter = True
    elif (906 <= pokemon_id <= 914):
        starter = True

    return starter

def check_if_evolves_further(evolution_chain_data, target_pokemon_name):
    if not evolution_chain_data or 'chain' not in evolution_chain_data:
        return False
    
# Helper function to recursively search the evolution chain
    def find_evolution_status(chain_link, target_name):
        current_species = chain_link['species']['name'].capitalize()
        
        # Check the current link
        if current_species == target_name:
            # If the 'evolves_to' list is NOT empty, it evolves further.
            return bool(chain_link.get('evolves_to'))

        # Recurse down the chain
        for evolves_to_link in chain_link.get('evolves_to', []):
            result = find_evolution_status(evolves_to_link, target_name)
            if result is not None:
                return result
                
        return None

    # Start the search from the base of the chain
    result = find_evolution_status(evolution_chain_data['chain'], target_pokemon_name)
    
    # Return True/False, defaulting to False if the Pokémon was not found in the chain
    return result if result is not None else False

def evolves_by_trading (pokemon_id):
    trade_evolution_list = [186,65,68,76,199,94,208,464,230,212,466,467,233,474,350,477,367,368,526,534,589,617,683,685,709,711]
    return pokemon_id in trade_evolution_list

def can_gigantamax (pokemon_id):
    gigantamax_list = [6, 12, 25, 52, 68, 94, 99, 131, 133, 143, 569, 809, 826, 834, 839, 841, 842, 844, 849, 851, 858, 861, 869, 879, 884, 3, 9, 812, 815, 818, 892]
    return pokemon_id in gigantamax_list

def main():
    # Loop through the first 151 Pokémon
    START_ID = 1
    END_ID = 1025
    
    print(f"--- Starting data collection for Pokémon IDs {START_ID} to {END_ID} ---")
    
    for pokemon_id in range(START_ID, END_ID + 1):
        # Get Core Data (Name, Stats, Types)
        base_info = call_pokemon_api(pokemon_id)
                

        # Get Species Data
        species_data = call_pokemon_species_api(pokemon_id)

        if base_info and species_data:
            # Data obtained from base_info api call
            name = base_info['name'].capitalize()
            types = [t['type']['name'].capitalize() for t in base_info['types']]

            # Sprites
            sprites_data = base_info.get('sprites', {})
            sprite_default = sprites_data.get('front_default')

            # Data obtained from Pokemon Location Areas

            # Data obtained from Pokemon Shapes

            # Data obtained from species_data api call
            egg_groups = [g['name'].capitalize() for g in species_data['egg_groups']]
            is_lengendary = species_data['is_legendary']
            is_mythical = species_data['is_mythical']
            is_baby = species_data['is_baby']

            parent_species_dict = species_data.get('evolves_from_species')
            evolves_from_name = parent_species_dict.get('name').capitalize() if parent_species_dict else None

            generation_num = generation_name_parser(species_data)

            primary_color_dict = species_data.get('color')
            primary_color = primary_color_dict.get('name').capitalize() 

            gender_rate = species_data.get('gender_rate')                           # male to female ratio (0 - 8), -1 = genderless

            # Check for mega evolution
            has_mega = mega_evolution_check(species_data)

            # Data obtained from evolution_chain api call
            chain_dict = species_data.get('evolution_chain')
            chain_url = chain_dict.get('url') if chain_dict else None
        
            evolves_further = False
            if chain_url: 
                try:
                    chain_id = int(chain_url.split('/')[-2])
                except (IndexError, ValueError):
                    chain_id = None
                    
                chain_data = call_evolution_chain_api(chain_url)
                
                if chain_data:
                    evolves_further = check_if_evolves_further(chain_data, name)
            else:
                chain_id = None

            region = region_finder(species_data)

            evolution_stone = None
            chain_id = None

            if chain_url and evolves_from_name:
                try:
                    chain_id = int(chain_url.split('/')[-2])
                except (IndexError, ValueError):
                    chain_id = None
                    
                chain_data = call_evolution_chain_api(chain_url)
                
                if chain_data and pokemon_id < 1010:                     # Bandaid solution
                    evolution_stone = get_evolution_stone(chain_data, name)

            fossile = is_fossile(pokemon_id)
            starter = is_starter(pokemon_id)
            evolves_from_trading = evolves_by_trading(pokemon_id)

            gigantmax = can_gigantamax(pokemon_id)
            
            # Leaving empty
            num_legs = 0
            popularity = 0

            # Structure the data
            pokemon_entry = {
                'ID': pokemon_id,
                'Name': name,
                'Type_1': types[0],
                'Type_2': types[1] if len(types) > 1 else None,
                'Primay_Color': primary_color,

                'Region': region,   
                'Generation': generation_num,
                'Lengendary': is_lengendary,
                'Mythical' : is_mythical,
                
                'Baby': is_baby,
                'Fossile': fossile,
                'Starter': starter,

                'Mega_Evolve': has_mega,
                'Gigantamax': gigantmax,
                
                'Gender_Rate': gender_rate/8 if (gender_rate >= 0) else -1,
                
                'Evolves': evolves_further,
                'Evolves_from': evolves_from_name if (evolves_from_name) else None, 
                'Evolves_from_stone': evolution_stone if (evolution_stone) else False,
                'Evolves_from_trading': evolves_from_trading,
                
                'Sprite_Default': sprite_default,

                'Number of Legs': num_legs,
                'Popularity': popularity
            }

            pokemon_data_list.append(pokemon_entry)
            print(f"{pokemon_id}: {name}")

            # Add some delay to the api inorder to limit the rate
            #time.sleep(0.01)

        else:
            print(f"Skipping ID {pokemon_id} due to failed API call.")


        
    print("\n--- Data Collection Complete ---")
    print(f"Successfully collected data for {len(pokemon_data_list)} Pokémon.")
    
    # Save the data to a JSON file
    with open('pokemon_data.json', 'w') as f:
        json.dump(pokemon_data_list, f, indent=4)
        
    print("Data saved to 'pokemon_data.json'")


if __name__ == "__main__":
    main()