import pandas as pd
from collections import Counter

# Load your data
df = pd.read_csv('lakers_2024_25.csv')

# Get all unique Lakers players
lakers_players = df[df['teamTricode'] == 'LAL'][['personId', 'playerName', 'playerNameI']].drop_duplicates()

# Function to get the display name (keeping suffix if present)
def get_display_name(full_name):
    parts = full_name.split()
    suffixes = ['III', 'IV', 'Jr.', 'Jr', 'Sr.', 'Sr', 'II']
    
    # If the last part is a suffix, keep it with the name
    if parts[-1] in suffixes and len(parts) > 1:
        # For "Trey Jemison III", return "Jemison III"
        return f"{parts[-2]} {parts[-1]}"
    else:
        # For "LeBron James", return "James"
        return parts[-1]

# Count last name occurrences to find duplicates
last_names = [get_display_name(name) for name in lakers_players['playerName']]
last_name_counts = Counter(last_names)

# Create a list for the clean data
clean_players = []

for _, row in lakers_players.iterrows():
    player_id = row['personId']
    full_name = row['playerName']
    abbrev_name = row['playerNameI']
    
    # Get the display name (keeping suffix if present)
    display_name = get_display_name(full_name)
    
    # Determine the best name to use
    if last_name_counts[display_name] > 1:
        # Last name is shared (like "James"), use abbreviated name
        best_name = abbrev_name
    else:
        # Last name is unique, use the display name
        best_name = display_name
    
    # Handle special characters (Dončić → Doncic)
    if 'č' in best_name:
        best_name = best_name.replace('č', 'c')
    
    clean_players.append({
        'personId': player_id,
        'playerName': best_name
    })

# Create DataFrame and save
clean_df = pd.DataFrame(clean_players)
clean_df = clean_df.sort_values('playerName')
clean_df.to_csv('lakers_players.csv', index=False)

# Print results
print("PLAYER LIST (personId → playerName)")
for _, row in clean_df.iterrows():
    print(f"  {row['personId']} → {row['playerName']}")
