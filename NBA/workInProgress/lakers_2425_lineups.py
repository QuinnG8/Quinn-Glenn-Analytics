import pandas as pd
import ast
# Load data
df = pd.read_csv('lakers_2024_25.csv')
starter_df = pd.read_csv('lakers_2024_25_quarter_starters.csv')
mapping_df = pd.read_csv('lakers_players.csv')

# Lookup Dictionary: Name → personId
name_to_id = {}
for _, row in mapping_df.iterrows():
    player_id = row['personId']
    variations = ast.literal_eval(row['name_variations'])
    for name in variations:
        name_to_id[name] = player_id


# Reverse lookup: personId → primary_name
id_to_name = {}
for _, row in mapping_df.iterrows():
    player_id = row['personId']
    primary_name = row['primary_name']
    id_to_name[player_id] = primary_name


# Parse a substitution
def parse_substitution(desc, name_to_id):
    """Parse substitution and return (in_id, out_id)."""
    if 'FOR' not in desc:
        return None, None
    
    parts = desc.split(' FOR ')
    in_player = parts[0].replace('SUB: ', '').strip()
    out_player = parts[1].strip()
    
    in_id = name_to_id.get(in_player)
    out_id = name_to_id.get(out_player)
    
    return in_id, out_id


luka_id = 1629029

# Dictionary of quarter starters by game
quarter_starters = {}
for _, row in starter_df.iterrows():
    game_id = row['GAME_ID']
    period = row['period']
    starter_ids = eval(row['starter_ids'])

    if game_id not in quarter_starters:
        quarter_starters[game_id] = {}

    quarter_starters[game_id][period] = set(starter_ids)

# Dictionary to track lineups
lineup_stints = {}

# Helper function to add or update a lineup
def add_lineup_stint(lineup_key):
    """Add a stint for a lineup or increment if it exists"""
    if lineup_key not in lineup_stints:
        lineup_stints[lineup_key] = {
            'stints': 0,
            'points_for': 0,
            'points_against': 0,
            'plus_minus': 0,
        }
    lineup_stints[lineup_key]['stints'] += 1

def add_points_to_lineup(lineup_key, points_for, points_against):
    """Add points scored and allowed for a lineup stint"""
    if lineup_key in lineup_stints:
        lineup_stints[lineup_key]['points_for'] += points_for
        lineup_stints[lineup_key]['points_against'] += points_against
        lineup_stints[lineup_key]['plus_minus'] += (points_for - points_against)
        

# Get all unique games
games = df['GAME_ID'].unique()
games = sorted(games)

for game_id in games: 
    print(f"\n Game {game_id}")

    game_df = df[df['GAME_ID'] == game_id].copy()
    game_df = game_df.sort_values(['period', 'actionNumber']).reset_index(drop=True)

    # Determine if Lakers are home or away
    lal_actions = game_df[game_df['teamTricode'] == 'LAL']
    if len(lal_actions) > 0:
        first_lal = lal_actions.iloc[0]
        is_home = (first_lal['location'] == 'h')
    else:
        is_home = False


    # Start with Q1 starters as current lineup
    current_lineup = None
    current_period = 1

    stint_start_lakers = 0
    stint_start_opponent = 0

    # Initialize with Q1 starters
    if game_id in quarter_starters and 1 in quarter_starters[game_id]:
        starters = quarter_starters[game_id][1]
        current_lineup = tuple(sorted(starters))
        
        # Record the start of the stint
        add_lineup_stint(current_lineup)
        stint_start_lakers = 0
        stint_start_opponent = 0

        player_names = [id_to_name.get(pid, str(pid)) for pid in current_lineup]
        print(f"Q1 Start: {', '.join(player_names)} → LINEUP STINTS: {lineup_stints[current_lineup]}")

    # Current scores we track throughout the game
    current_lakers = 0
    current_opponent = 0

    # Loop through each action
    for idx, action in game_df.iterrows():
        
        if is_home:
            if pd.notna(action['scoreHome']):
                current_lakers = action['scoreHome']
            if pd.notna(action['scoreAway']):
                current_opponent = action['scoreAway']
        else:
            if pd.notna(action['scoreHome']):
                current_opponent = action['scoreHome']
            if pd.notna(action['scoreAway']):
                current_lakers = action['scoreAway']
            

        
        period = action['period']

        # Check if period changed
        if period != current_period:
            current_period = period

            # End current stint by adding points
            if current_lineup is not None:
                points_for = current_lakers - stint_start_lakers
                points_against = current_opponent - stint_start_opponent
                add_points_to_lineup(current_lineup, points_for, points_against)
                
                # Print stint summary
                player_names = [id_to_name.get(pid,str(pid)) for pid in current_lineup]
                print(f"Q{period - 1} END: {', '.join(player_names)} → +/-: {points_for - points_against}")

            # Start new quarter with new lineup
            if game_id in quarter_starters and period in quarter_starters[game_id]:
                starters = quarter_starters[game_id][period]
                new_lineup = tuple(sorted(starters))
                if new_lineup != current_lineup:
                    current_lineup = new_lineup
                    add_lineup_stint(current_lineup)

                    # Restart scoring stint
                    stint_start_lakers = current_lakers
                    stint_start_opponent = current_opponent

                    player_names = [id_to_name.get(pid, str(pid)) for pid in current_lineup]
                    print(f"  Q{period} Start: {', '.join(player_names)} → LINEUP STINTS: {lineup_stints[current_lineup]['stints']}")

        
        # Check for substitution
        if action['actionType'] == 'Substitution' and action['teamTricode'] == 'LAL':
            desc = action['description']
            in_id, out_id = parse_substitution(desc, name_to_id)

            if in_id is not None and out_id is not None and current_lineup is not None:
                # End current stint by adding points
                points_for = current_lakers - stint_start_lakers
                points_against = current_opponent - stint_start_opponent
                add_points_to_lineup(current_lineup, points_for, points_against)

                # Print stint summary
                player_names = [id_to_name.get(pid, str(pid)) for pid in current_lineup]
                print(f"  STINT END: {', '.join(player_names)} → {points_for - points_against}")
                
                # Update lineup
                new_lineup_list = list(current_lineup)
                if out_id in new_lineup_list:
                    new_lineup_list.remove(out_id)
                if in_id not in new_lineup_list:
                    new_lineup_list.append(in_id)
                
                # Sort our new lineup
                new_lineup = tuple(sorted(new_lineup_list))

                # Make sure lineup changed and has 5 players
                if len(new_lineup) == 5 and new_lineup != current_lineup:
                    current_lineup = new_lineup
                    add_lineup_stint(current_lineup)
                    
                    # Restart the stint
                    stint_start_lakers = current_lakers
                    stint_start_opponent = current_opponent

                    # Printing new lineup
                    in_name = id_to_name.get(in_id, str(in_id))
                    out_name = id_to_name.get(out_id, str(out_id))

                    player_names = [id_to_name.get(pid, str(pid)) for pid in current_lineup]

                    print(f"SUB: {in_name} IN, {out_name} OUT → {', '.join(player_names)} → LINEUP STINTS: {lineup_stints[current_lineup]}")

    # End of game, point differential for last stint
    if current_lineup is not None:
        points_for = current_lakers - stint_start_lakers
        points_against = current_opponent - stint_start_opponent
        add_points_to_lineup(current_lineup, points_for, points_against)

        player_names = [id_to_name.get(pid, str(pid)) for pid in current_lineup]
        print(f"  GAME END: {', '.join(player_names)} → {points_for - points_against}")



print(f"Total unique lineups: {len(lineup_stints)}")
print(f"Total stints: {sum(v['stints'] for v in lineup_stints.values())}")
