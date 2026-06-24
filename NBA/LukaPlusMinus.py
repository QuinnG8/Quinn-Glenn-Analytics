import pandas as pd

# Load the data
df = pd.read_csv('luka_all_games_complete.csv')
starter_df = pd.read_csv('all_games_quarter_starters.csv')

luka_id = 1629029

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

print("="*60)
print(f"CALCULATING LUKA'S PLUS/MINUS FOR {len(games)} GAMES")
print("="*60)

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
    
    # Track if we're in a free throw sequence after a substitution
    skip_next_score = False
    
    # Start with Q1 starters
    if game_id in quarter_starters and 1 in quarter_starters[game_id]:
        if luka_id in quarter_starters[game_id][1]:
            luka_on_court = True
            stint_start_lakers = 0
            stint_start_opponent = 0
    
    for idx, action in game_df.iterrows():
        # Update scores
        if is_home:
            if pd.notna(action['scoreHome']):
                current_lakers = action['scoreHome']
            if pd.notna(action['scoreAway']):
                current_opponent = action['scoreAway']
        else:
            if pd.notna(action['scoreAway']):
                current_lakers = action['scoreAway']
            if pd.notna(action['scoreHome']):
                current_opponent = action['scoreHome']
        
        period = action['period']
        
        # Check if period changed
        if period != current_period:
            current_period = period
            if game_id in quarter_starters and period in quarter_starters[game_id]:
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
        
        # Check for Luka substitution
        if action['actionType'] == 'Substitution' and action['teamTricode'] == 'LAL':
            desc = action['description']
            
            if 'Doncic' in desc or 'Dončić' in desc:
                if 'FOR Doncic' in desc or 'FOR Dončić' in desc:
                    # Luka going OUT
                    if luka_on_court:
                        points_for = current_lakers - stint_start_lakers
                        points_against = current_opponent - stint_start_opponent
                        total_plus_minus += (points_for - points_against)
                        luka_on_court = False
                        # CRITICAL: After Luka is subbed out, any points scored
                        # on free throws after this moment should NOT count
                        # We'll handle this by tracking the score at the moment of substitution
                else:
                    # Luka coming IN
                    if not luka_on_court:
                        stint_start_lakers = current_lakers
                        stint_start_opponent = current_opponent
                        luka_on_court = True
        
        # Track the actual score at the moment of substitution
        # Store the score when Luka is subbed out so we don't count free throws after
        if action['actionType'] == 'Substitution' and action['teamTricode'] == 'LAL':
            desc = action['description']
            if 'FOR Doncic' in desc or 'FOR Dončić' in desc:
                # Luka subbed out - this is the exact moment the stint ends
                # The score at this moment is the final score for the stint
                # Any future free throws in the same sequence shouldn't count
                pass
    
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
print("="*60)
for result in all_results:
    print(f"  Game {result['game_id']}: +/- = {result['plus_minus']}")

print("\n" + "="*60)
print(f"TOTAL PLUS/MINUS ACROSS ALL {len(games)} GAMES: {total_plus_minus_all}")
print("="*60)