import pandas as pd

# Load the game data
df = pd.read_csv('luka_first_game_with_quarters.csv')

# Get quarter starters from the existing data
quarter_starters = {}

for period in [1, 2, 3, 4]:
    period_df = df[df['period'] == period]
    
    # Get the first 5 unique LAL players in this quarter
    starters = []
    seen = set()
    
    for idx, action in period_df.iterrows():
        if action['teamTricode'] == 'LAL' and action['personId'] != 0:
            if action['personId'] not in seen:
                seen.add(action['personId'])
                starters.append(action['personId'])
                if len(starters) == 5:
                    break
    
    quarter_starters[period] = starters

# Save quarter starters to CSV
starter_df = pd.DataFrame([
    {'period': p, 'starter_ids': str(ids)} 
    for p, ids in quarter_starters.items()
])
starter_df.to_csv('quarter_starters.csv', index=False)

print("Quarter starters saved to quarter_starters.csv")
for p, ids in quarter_starters.items():
    names = []
    for pid in ids:
        name_row = df[df['personId'] == pid].iloc[0] if len(df[df['personId'] == pid]) > 0 else None
        if name_row is not None:
            names.append(name_row['playerName'])
    print(f"Q{p}: {names}")



# Load the data
df = pd.read_csv('luka_first_game_with_quarters.csv')
starter_df = pd.read_csv('quarter_starters.csv')

luka_id = 1629029

# Create a dictionary of quarter starters
quarter_starters = {}
for _, row in starter_df.iterrows():
    period = row['period']
    starter_ids = eval(row['starter_ids'])
    quarter_starters[period] = set(starter_ids)

# Sort by period and action
df = df.sort_values(['period', 'actionNumber'])

# Track Luka's status
luka_on_court = True  # He starts Q1
stint_start_home = 0
stint_start_away = 0
total_plus_minus = 0

current_home = 0
current_away = 0
current_period = 1

print("="*60)
print("LUKA'S PLUS/MINUS USING QUARTER STARTERS")
print("="*60)

# Start with Q1 starters
if luka_id in quarter_starters[1]:
    luka_on_court = True
    stint_start_home = 0
    stint_start_away = 0
    print(f"Q1 START: Luka is ON the court at 0-0")
else:
    luka_on_court = False
    print(f"Q1 START: Luka is NOT on the court")

for idx, action in df.iterrows():
    # Update scores
    if pd.notna(action['scoreHome']):
        current_home = action['scoreHome']
    if pd.notna(action['scoreAway']):
        current_away = action['scoreAway']
    
    period = action['period']
    
    # Check if period changed
    if period != current_period:
        current_period = period
        # Reset Luka's status based on quarter starters
        if luka_id in quarter_starters[period]:
            if not luka_on_court:
                # Luka is starting this quarter - start a new stint
                luka_on_court = True
                stint_start_home = current_home
                stint_start_away = current_away
                print(f"\nQ{period} START: Luka is ON the court at {current_home}-{current_away}")
            else:
                # Luka was already on court - continue
                print(f"\nQ{period} START: Luka continues on the court at {current_home}-{current_away}")
        else:
            if luka_on_court:
                # Luka was on court but is NOT in quarter starters
                # This shouldn't happen, but if it does, end the stint
                points_for = current_home - stint_start_home
                points_against = current_away - stint_start_away
                total_plus_minus += (points_for - points_against)
                print(f"Q{period} START: Luka is OFF the court | Stint +/-: {points_for - points_against}")
                luka_on_court = False
    
    # Check for Luka substitution
    if action['actionType'] == 'Substitution' and action['teamTricode'] == 'LAL':
        desc = action['description']
        
        # If Luka is mentioned
        if 'Doncic' in desc or 'Dončić' in desc:
            if 'FOR Doncic' in desc or 'FOR Dončić' in desc:
                # Luka is going OUT
                if luka_on_court:
                    points_for = current_home - stint_start_home
                    points_against = current_away - stint_start_away
                    total_plus_minus += (points_for - points_against)
                    print(f"Luka OUT at {current_home}-{current_away} | +/-: {points_for - points_against}")
                    luka_on_court = False
            else:
                # Luka is coming IN
                if not luka_on_court:
                    stint_start_home = current_home
                    stint_start_away = current_away
                    print(f"Luka IN at {current_home}-{current_away}")
                    luka_on_court = True

# End of game
if luka_on_court:
    points_for = current_home - stint_start_home
    points_against = current_away - stint_start_away
    total_plus_minus += (points_for - points_against)
    print(f"\nGame END at {current_home}-{current_away} | Final +/-: {points_for - points_against}")

print("\n" + "="*60)
print(f"LUKA'S TOTAL PLUS/MINUS: {total_plus_minus}")
print("EXPECTED: +15")
print("="*60)