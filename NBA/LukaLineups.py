import pandas as pd
from collections import defaultdict

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

# Get all games
games = df['GAME_ID'].unique()
games = sorted(games)

print("="*60)
print(f"TRACKING LUKA'S LINEUP STINTS AND POSSESSIONS FOR {len(games)} GAMES")
print("="*60)

# Track all lineups across all games
lineup_data = defaultdict(lambda: {
    'stints': 0,
    'offensive_possessions': 0,
    'defensive_possessions': 0,
    'points_for': 0,
    'points_against': 0
})

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
    
    # Track current lineup
    current_lineup = None
    luka_on_court = False
    current_period = 1
    
    # Keep track of players on court
    players_on_court = set()
    
    # Track stint data
    stint_start_lakers = 0
    stint_start_opponent = 0
    stint_offensive_poss = 0
    stint_defensive_poss = 0
    current_lineup_tuple = None
    
    # Track free throw sequences
    ft_sequence_active = False
    
    # Start with Q1 starters
    if game_id in quarter_starters and 1 in quarter_starters[game_id]:
        if luka_id in quarter_starters[game_id][1]:
            luka_on_court = True
            starters = [p for p in quarter_starters[game_id][1] if p != luka_id]
            current_lineup_tuple = tuple(sorted(starters))
            current_lineup = set(starters)
            stint_start_lakers = 0
            stint_start_opponent = 0
            stint_offensive_poss = 0
            stint_defensive_poss = 0
    
    for idx, action in game_df.iterrows():
        # Update scores first
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
        player_id = action['personId']
        team = action['teamTricode']
        action_type = action['actionType']
        
        # Check if free throw sequence starts
        if action_type == 'Free Throw' and not ft_sequence_active:
            ft_sequence_active = True
        
        # Check if period changed
        if period != current_period:
            # End current stint if Luka was on court
            if luka_on_court and current_lineup_tuple is not None:
                # Record the stint data
                points_for = current_lakers - stint_start_lakers
                points_against = current_opponent - stint_start_opponent
                lineup_data[current_lineup_tuple]['stints'] += 1
                lineup_data[current_lineup_tuple]['offensive_possessions'] += stint_offensive_poss
                lineup_data[current_lineup_tuple]['defensive_possessions'] += stint_defensive_poss
                lineup_data[current_lineup_tuple]['points_for'] += points_for
                lineup_data[current_lineup_tuple]['points_against'] += points_against
            
            current_period = period
            # Reset for new quarter
            if game_id in quarter_starters and period in quarter_starters[game_id]:
                if luka_id in quarter_starters[game_id][period]:
                    luka_on_court = True
                    starters = [p for p in quarter_starters[game_id][period] if p != luka_id]
                    current_lineup_tuple = tuple(sorted(starters))
                    current_lineup = set(starters)
                    stint_start_lakers = current_lakers
                    stint_start_opponent = current_opponent
                    stint_offensive_poss = 0
                    stint_defensive_poss = 0
                else:
                    luka_on_court = False
                    current_lineup_tuple = None
                    current_lineup = None
        
        # Handle substitutions
        if action_type == 'Substitution' and team == 'LAL':
            desc = action['description']
            
            # Check if it's a Luka substitution
            if 'Doncic' in desc or 'Dončić' in desc:
                if 'FOR Doncic' in desc or 'FOR Dončić' in desc:
                    # Luka going OUT - end the stint
                    if luka_on_court and current_lineup_tuple is not None:
                        # Record the stint data
                        points_for = current_lakers - stint_start_lakers
                        points_against = current_opponent - stint_start_opponent
                        lineup_data[current_lineup_tuple]['stints'] += 1
                        lineup_data[current_lineup_tuple]['offensive_possessions'] += stint_offensive_poss
                        lineup_data[current_lineup_tuple]['defensive_possessions'] += stint_defensive_poss
                        lineup_data[current_lineup_tuple]['points_for'] += points_for
                        lineup_data[current_lineup_tuple]['points_against'] += points_against
                    luka_on_court = False
                    current_lineup_tuple = None
                    current_lineup = None
                else:
                    # Luka coming IN - start a new stint
                    if not luka_on_court:
                        luka_on_court = True
                        # Get current players on court
                        lakers_in_actions = set()
                        for j in range(max(0, idx-30), idx):
                            if game_df.iloc[j]['teamTricode'] == 'LAL':
                                pid = game_df.iloc[j]['personId']
                                if pid != 0 and pid != luka_id:
                                    lakers_in_actions.add(pid)
                        if len(lakers_in_actions) >= 4:
                            current_lineup_tuple = tuple(sorted(list(lakers_in_actions)[:4]))
                            current_lineup = set(lakers_in_actions)
                            stint_start_lakers = current_lakers
                            stint_start_opponent = current_opponent
                            stint_offensive_poss = 0
                            stint_defensive_poss = 0
            else:
                # Regular substitution - update players on court
                if 'FOR' in desc:
                    parts = desc.split(' FOR ')
                    if len(parts) == 2:
                        in_player = parts[0].replace('SUB: ', '').strip()
                        out_player = parts[1].strip()
                        
                        # Find their IDs
                        in_id = None
                        out_id = None
                        
                        in_rows = df[df['playerName'].str.contains(in_player, case=False, na=False)]
                        if len(in_rows) > 0:
                            in_id = in_rows.iloc[0]['personId']
                        
                        out_rows = df[df['playerName'].str.contains(out_player, case=False, na=False)]
                        if len(out_rows) > 0:
                            out_id = out_rows.iloc[0]['personId']
                        
                        # Update players on court
                        if in_id and in_id != 0 and in_id != luka_id:
                            players_on_court.add(in_id)
                        if out_id and out_id != 0 and out_id != luka_id:
                            players_on_court.discard(out_id)
                        
                        # If Luka is on court and we have 4 teammates, update the lineup
                        if luka_on_court:
                            teammates = tuple(sorted([p for p in players_on_court if p != luka_id]))
                            if len(teammates) == 4 and teammates != current_lineup_tuple:
                                # End current stint
                                if current_lineup_tuple is not None:
                                    points_for = current_lakers - stint_start_lakers
                                    points_against = current_opponent - stint_start_opponent
                                    lineup_data[current_lineup_tuple]['stints'] += 1
                                    lineup_data[current_lineup_tuple]['offensive_possessions'] += stint_offensive_poss
                                    lineup_data[current_lineup_tuple]['defensive_possessions'] += stint_defensive_poss
                                    lineup_data[current_lineup_tuple]['points_for'] += points_for
                                    points_for = 0
                                    points_against = 0
                                
                                # Start new stint with new lineup
                                current_lineup_tuple = teammates
                                current_lineup = set(teammates)
                                stint_start_lakers = current_lakers
                                stint_start_opponent = current_opponent
                                stint_offensive_poss = 0
                                stint_defensive_poss = 0
        
        # Count possessions while Luka is on court
        if luka_on_court and current_lineup_tuple is not None:
            # Track free throw sequences - only count the LAST free throw
            if action_type == 'Free Throw':
                if ft_sequence_active:
                    # Check if this is the last free throw in the sequence
                    if idx < len(game_df) - 1:
                        next_action = game_df.iloc[idx + 1]
                        if next_action['actionType'] != 'Free Throw':
                            # This is the last free throw - count it
                            ft_sequence_active = False
                            if team == 'LAL':
                                stint_offensive_poss += 1
                            else:
                                stint_defensive_poss += 1
                    else:
                        # End of game, this is the last free throw
                        if team == 'LAL':
                            stint_offensive_poss += 1
                        else:
                            stint_defensive_poss += 1
            
            # Count made shots (possession ends)
            elif action_type == 'Made Shot':
                if team == 'LAL':
                    stint_offensive_poss += 1
                else:
                    stint_defensive_poss += 1
            
            # Count missed shots - but ONLY if followed by a defensive rebound
            elif action_type == 'Missed Shot':
                if idx < len(game_df) - 1:
                    next_action = game_df.iloc[idx + 1]
                    if next_action['actionType'] == 'Rebound':
                        if team == 'LAL':
                            if next_action['teamTricode'] != 'LAL':
                                stint_offensive_poss += 1
                        else:
                            if next_action['teamTricode'] == 'LAL':
                                stint_defensive_poss += 1
            
            # Count turnovers (possession ends)
            elif action_type == 'Turnover':
                if team == 'LAL':
                    stint_offensive_poss += 1
                else:
                    stint_defensive_poss += 1
    
    # End of game - record final stint
    if luka_on_court and current_lineup_tuple is not None:
        points_for = current_lakers - stint_start_lakers
        points_against = current_opponent - stint_start_opponent
        lineup_data[current_lineup_tuple]['stints'] += 1
        lineup_data[current_lineup_tuple]['offensive_possessions'] += stint_offensive_poss
        lineup_data[current_lineup_tuple]['defensive_possessions'] += stint_defensive_poss
        lineup_data[current_lineup_tuple]['points_for'] += points_for
        lineup_data[current_lineup_tuple]['points_against'] += points_against

# Print summary
print("\n" + "="*60)
print("LINEUP SUMMARY WITH POSSESSIONS")
print("="*60)

# Convert to DataFrame for display
results = []
for lineup_tuple, data in lineup_data.items():
    names = []
    for pid in lineup_tuple:
        name_row = df[df['personId'] == pid]
        if len(name_row) > 0:
            names.append(name_row.iloc[0]['playerName'])
    
    total_poss = data['offensive_possessions'] + data['defensive_possessions']
    results.append({
        'lineup': ', '.join(names),
        'stints': data['stints'],
        'off_poss': data['offensive_possessions'],
        'def_poss': data['defensive_possessions'],
        'total_poss': total_poss,
        'points_for': data['points_for'],
        'points_against': data['points_against'],
        'plus_minus': data['points_for'] - data['points_against']
    })

results_df = pd.DataFrame(results)
results_df = results_df.sort_values('stints', ascending=False)

print("\nTOP 10 MOST USED LINEUPS:")
print(results_df[['lineup', 'stints', 'off_poss', 'def_poss', 'total_poss', 'plus_minus']].head(10).to_string(index=False))

print("\n" + "="*60)
print(f"Total unique lineups: {len(lineup_data)}")
print(f"Total stints: {sum(d['stints'] for d in lineup_data.values())}")
print(f"Total offensive possessions: {sum(d['offensive_possessions'] for d in lineup_data.values())}")
print(f"Total defensive possessions: {sum(d['defensive_possessions'] for d in lineup_data.values())}")
print("="*60)