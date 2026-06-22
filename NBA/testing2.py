from nba_api.stats.endpoints import boxscoretraditionalv3
import pandas as pd

game_id = '0022401185'

print(f"TESTING BOX SCORE DATA FOR GAME: {game_id}")
print("="*60)

try:
    boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
    player_stats = boxscore.player_stats.get_data_frame()
    
    print(f"\nTotal players in box score: {len(player_stats)}")
    print(f"Columns: {player_stats.columns.tolist()}")
    
    print("\n" + "="*60)
    print("LAKERS PLAYERS - FULL DATA")
    print("="*60)
    
    # Show all Lakers players with relevant columns
    lakers = player_stats[player_stats['teamTricode'] == 'LAL']
    
    # Convert minutes to seconds for sorting
    def min_to_sec(min_str):
        try:
            if pd.isna(min_str) or min_str == '':
                return -1
            if ':' in min_str:
                parts = min_str.split(':')
                return int(parts[0]) * 60 + int(parts[1])
            return -1
        except:
            return -1
    
    lakers['minutes_seconds'] = lakers['minutes'].apply(min_to_sec)
    
    # Sort by minutes played
    lakers_sorted = lakers.sort_values('minutes_seconds', ascending=False)
    
    print("\nAll Lakers players (sorted by minutes played):")
    print("-"*80)
    for idx, row in lakers_sorted.iterrows():
        name = f"{row['firstName']} {row['familyName']}"
        print(f"  {name:25} | Minutes: {row['minutes']:>8} | Points: {row['points']:>3} | Comment: '{row['comment']}'")
    
    print("\n" + "="*60)
    print("CHECKING IF THERE'S ANY STARTER INDICATOR")
    print("="*60)
    
    # Check if any column has starter info
    for col in player_stats.columns:
        if 'start' in col.lower() or 'lineup' in col.lower():
            print(f"Found column: {col}")
            print(f"  Values: {player_stats[col].unique()}")
    
    # Check the raw data for the first few players
    print("\n" + "="*60)
    print("RAW DATA FOR FIRST 5 ROWS")
    print("="*60)
    print(player_stats.head(5).to_dict('records'))
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()