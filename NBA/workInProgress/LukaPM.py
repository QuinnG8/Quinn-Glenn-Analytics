import pandas as pd
import ast


# Load data
df = pd.read_csv('lakers_2024_25.csv')
starter_df = pd.read_csv('lakers_2024_25_quarter_starters.csv')
mapping_df = pd.read_csv('lakers_players.csv')

# Build lookup dictionary: name → personId
name_to_id = {}
for _, row in mapping_df.iterrows():
    player_id = row['personId']
    variations = ast.literal_eval(row['name_variations'])
    for name in variations:
        name_to_id[name] = player_id

luka_id = 1629029


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

# Create a dictionary of quarter starters by game
quarter_starters = {}
for _, row in starter_df.iterrows():
    game_id = row['GAME_ID']
    period = row['period']
    starter_ids = eval(row['starter_ids'])

    if game_id not in quarter_starters:
        quarter_starters[game_id] = {}

    quarter_starters[game_id][period] = set(starter_ids)

# Get all unique games
games = df['GAME_ID'].unique()
games = sorted(games)

print("Calculating Luka's Plus/Minus for the 2024/2025 season")

all_results = []
total_plus_minus_all = 0

for game_id in games:
    game_df = df[df['GAME_ID'] == game_id].copy()
    game_df = game_df.sort_values(['period', 'actionNumber']).reset_index(drop=True)

    # Determine if Lakers are home or away
    lal_actions = game_df[game_df['teamTricode'] == 'LAL']
    if len(lal_actions) > 0:
        first_lal = lal_actions.iloc[0]
        is_home = (first_lal['location'] == 'h')
    else:
        is_home = False
    
    # Track Luka's status
    luka_on_court = False
    stint_start_lakers = 0
    stint_start_opponent = 0
    total_plus_minus = 0

    current_lakers = 0
    current_opponent = 0
    current_period = 1

    if game_id in quarter_starters and 1 in quarter_starters[game_id]:
        if luka_id in quarter_starters[game_id][1]:
            luka_on_court = True
            stint_start_lakers = 0
            stint_start_opponent = 0
        
    for idx, action in game_df.iterrows():
        # Updating scores
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
            if luka_id in quarter_starters[game_id][period]:
                if not luka_on_court:
                    luka_on_court = True
                    stint_start_lakers = current_lakers
                    stint_start_opponent = current_opponent
            else:
                if luka_on_court:
                    points_for = current_lakers - stint_start_lakers
                    points_against = current_opponent - stint_start_opponent
                    total_plus_minus += (points_for - points_against)
                    luka_on_court = False

        # Check for Luka being subbed
        if action['actionType'] == 'Substitution' and action['teamTricode'] == 'LAL':
            desc = action['description']
            in_id, out_id = parse_substitution(desc, name_to_id)
            # Check if Luka is involved
            if in_id == luka_id or out_id == luka_id:
                if out_id == luka_id:
                    if luka_on_court:
                        points_for = current_lakers - stint_start_lakers
                        points_against = current_opponent - stint_start_opponent

                        total_plus_minus += (points_for - points_against)
                        luka_on_court = False
                elif in_id == luka_id:
                    if not luka_on_court:
                        stint_start_lakers = current_lakers
                        stint_start_opponent = current_opponent
                        luka_on_court = True


    # End of game
    if luka_on_court:
        points_for = current_lakers - stint_start_lakers
        points_against = current_opponent - stint_start_opponent
        total_plus_minus += (points_for - points_against)


    all_results.append({
        'game_id': game_id, 
        'plus_minus': total_plus_minus
    })
    
    total_plus_minus_all += total_plus_minus

# Print results
print("\n" + "="*60)
print("RESULTS BY GAME")
for result in all_results:
    print(f"  Game {result['game_id']}: +/- = {result['plus_minus']}")

print(f"TOTAL PLUS/MINUS ACROSS ALL {len(games)} GAMES: {total_plus_minus_all}")