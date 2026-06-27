import pandas as pd

# Load data
df = pd.read_csv('lakers_2024_25.csv')
starter_df = pd.read_csv('lakers_2024_25_quarter_starters.csv')

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

print("Calculating Luka's Plus/Minus for the 2024/2025 season")

all_results = []
total_plus_minus = 0

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
    
    
