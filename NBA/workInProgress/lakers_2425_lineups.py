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

# Get all unique games
games = df['GAME_ID'].unique()
games = sorted(games)

for game_id in games: 
    print(f"\n Game {game_id}")

    game_df = df[df['GAME_ID'] == game_id].copy()
    game_df = game_df.sort_values(['period', 'actionNumber']).reset_index(drop=True)

    # Start with Q1 starters as current lineup
    current_lineup = None
    current_period = 1

    # Initialize with Q1 starters
    if game_id in quarter_starters and 1 in quarter_starters[game_id]:
        starters = quarter_starters[game_id][1]
        current_lineup = tuple(sorted(starters))
        if current_lineup not in lineup_stints:
            lineup_stints[current_lineup] = 0
        lineup_stints[current_lineup] += 1

        player_names = [id_to_name.get(pid, str(pid)) for pid in current_lineup]
        print(f"Q1 Start: {', '.join(player_names)}")

    # Loop through each action
    for idx, action in game_df.iterrows():
        period = action['period']

        # Check if period changed
        if period != current_period:
            current_period = period
            if game_id in quarter_starters and period in quarter_starters[game_id]:
                starters = quarter_starters[game_id][period]
                new_lineup = tuple(sorted(starters))
                if new_lineup != current_lineup:
                    current_lineup = new_lineup
                    if current_lineup not in lineup_stints:
                        lineup_stints[current_lineup] = 0
                    lineup_stints[current_lineup] += 1

                    player_names = [id_to_name.get(pid, str(pid)) for pid in current_lineup]
                    print(f"  Q{period} Start: {', '.join(player_names)}")

        
        # Check for substitution
        if action['actionType'] == 'Substitution' and action['teamTricode'] == 'LAL':
            desc = action['description']
            in_id, out_id = parse_substitution(desc, name_to_id)

            if in_id is not None and out_id is not None:
                # Update current lineup
                new_lineup_list = list(current_lineup) if current_lineup else []
                if out_id in new_lineup_list:
                    new_lineup_list.remove(out_id)
                if in_id not in new_lineup_list:
                    new_lineup_list.append(in_id)

                new_lineup = tuple(sorted(new_lineup_list))

                # Make sure lineup changed and has 5 players
                if len(new_lineup) == 5 and new_lineup != current_lineup:
                    current_lineup = new_lineup
                    if current_lineup not in lineup_stints:
                        lineup_stints[current_lineup] = 0
                    lineup_stints[current_lineup] += 1

                    # Printing new lineup
                    in_name = id_to_name.get(in_id, str(in_id))
                    out_name = id_to_name.get(out_id, str(out_id))

                    player_names = [id_to_name.get(pid, str(pid)) for pid in current_lineup]

                    print(f"SUB: {in_name} IN, {out_name} OUT → {', '.join(player_names)} → LINEUP STINTS: {lineup_stints[current_lineup]}")



print(f"Total unique lineups: {len(lineup_stints)}")
print(f"Total stints: {sum(lineup_stints.values())}")
