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
    
    if parts[-1] in suffixes and len(parts) > 1:
        return f"{parts[-2]} {parts[-1]}"
    else:
        return parts[-1]

# Count last name occurrences to find duplicates
last_names = [get_display_name(name) for name in lakers_players['playerName']]
last_name_counts = Counter(last_names)

# Create a list for the final data
player_data = []

for _, row in lakers_players.iterrows():
    player_id = row['personId']
    full_name = row['playerName']
    abbrev_name = row['playerNameI']
    
    # Get the display name
    display_name = get_display_name(full_name)
    
    # Determine the primary name
    if last_name_counts[display_name] > 1:
        primary_name = abbrev_name
    else:
        primary_name = display_name
    
    # Clean special characters for primary name
    primary_name_clean = primary_name.replace('č', 'c')
    
    # Collect ALL variations for this player
    variations = set()
    
    # 1. Full name
    variations.add(full_name)
    
    # 2. Abbreviated name
    variations.add(abbrev_name)
    
    # 3. Primary name (with special characters)
    variations.add(primary_name)
    
    # 4. Primary name (cleaned)
    variations.add(primary_name_clean)
    
    # 5. Last name only (as fallback)
    variations.add(display_name)
    
    # 6. Clean version of last name (for Dončić → Doncic)
    variations.add(display_name.replace('č', 'c'))
    
    # Remove any empty or None values
    variations = {v for v in variations if v and v != ''}
    
    # Sort variations for consistency
    variations_list = sorted(list(variations))
    
    player_data.append({
        'personId': player_id,
        'primary_name': primary_name_clean,
        'name_variations': str(variations_list)  # Save as string for CSV
    })

# Create DataFrame
final_df = pd.DataFrame(player_data)
final_df = final_df.sort_values('primary_name')

# Save to CSV
final_df.to_csv('lakers_players.csv', index=False)

