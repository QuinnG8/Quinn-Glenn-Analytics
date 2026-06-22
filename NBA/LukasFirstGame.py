from nba_api.stats.endpoints import leaguegamefinder, playbyplayv3, boxscoretraditionalv3
from nba_api.stats.static import teams
import pandas as pd
import time

# Get Lakers team ID
lakers = teams.find_team_by_abbreviation('LAL')
lakers_id = lakers['id']
print(f"Lakers Team ID: {lakers_id}")

# Get Lakers games for 2024-25
season = '2024-25'
gamefinder = leaguegamefinder.LeagueGameFinder(
    team_id_nullable=lakers_id,
    season_nullable=season
)
games_df = gamefinder.get_data_frames()[0]
regular_season = games_df[games_df['GAME_ID'].str.startswith('002')]
print(f"Found {len(regular_season)} regular season games")

# Look at games from Feb 2025 onwards
regular_season = regular_season.copy()
regular_season['GAME_DATE'] = pd.to_datetime(regular_season['GAME_DATE'])
post_trade_games = regular_season[regular_season['GAME_DATE'] >= '2025-02-01']
print(f"Games from Feb 2025 onwards: {len(post_trade_games)}")

# Find Luka's FIRST game
first_luka_game_id = None
games_to_check = post_trade_games['GAME_ID'].tolist()

print("\nFinding Luka's first game...")
for idx, game_id in enumerate(games_to_check, 1):
    print(f"  Checking game {idx}/{len(games_to_check)}: {game_id}", end='')
    
    try:
        pbp = playbyplayv3.PlayByPlayV3(game_id=game_id)
        pbp_df = pbp.get_data_frames()[0]
        
        # Check for "Dončić" or "Doncic" in player names
        has_luka = pbp_df['playerName'].str.contains('Dončić|Doncic', case=False, na=False).any()
        
        if has_luka:
            print(f" ✓ Luka found! This is his first game in the data.")
            first_luka_game_id = game_id
            break
        else:
            print(f" - No Luka")
            
        time.sleep(0.3)
        
    except Exception as e:
        print(f" ✗ Error: {e}")

if first_luka_game_id:
    print(f"\n✅ Found Luka's first game: {first_luka_game_id}")
    
    # Fetch the play-by-play for just this game
    print("\n" + "="*60)
    print("FETCHING PLAY-BY-PLAY FOR LUKA'S FIRST GAME")
    print("="*60)
    
    pbp = playbyplayv3.PlayByPlayV3(game_id=first_luka_game_id)
    pbp_df = pbp.get_data_frames()[0]
    pbp_df['GAME_ID'] = first_luka_game_id
    
    # DETECT STARTERS FOR EACH QUARTER
    print("\n" + "="*60)
    print("DETECTING STARTERS FOR EACH QUARTER")
    print("="*60)
    
    # Sort by period and action
    pbp_df = pbp_df.sort_values(['period', 'actionNumber'])
    
    # Track quarter starters
    quarter_starters = {}
    current_period = 1
    players_seen = set()
    
    for idx, action in pbp_df.iterrows():
        period = action['period']
        team = action['teamTricode']
        player_id = action['personId']
        player_name = action['playerName']
        
        # If period changed, reset for new quarter
        if period != current_period:
            current_period = period
            players_seen = set()
            print(f"\nQ{period} - Detecting starters...")
        
        # If it's a LAL player and we haven't seen them yet
        if team == 'LAL' and player_id != 0 and player_id not in players_seen:
            players_seen.add(player_id)
            
            # If we have 5 players, we found the starters for this quarter
            if len(players_seen) == 5:
                quarter_starters[period] = list(players_seen)
                print(f"  Q{period} starters: {players_seen}")
                # Don't break - continue to get player names
    
    # Add quarter starters info to the dataframe
    def get_quarter_starters(row):
        period = row['period']
        if period in quarter_starters:
            return str(quarter_starters[period])
        return ''
    
    pbp_df['quarter_starters'] = pbp_df.apply(get_quarter_starters, axis=1)
    
    # Also add player names for readability
    def get_starter_names(row):
        period = row['period']
        if period in quarter_starters:
            names = []
            for pid in quarter_starters[period]:
                name_row = pbp_df[pbp_df['personId'] == pid].iloc[0] if len(pbp_df[pbp_df['personId'] == pid]) > 0 else None
                if name_row is not None:
                    names.append(name_row['playerName'])
            return ', '.join(names)
        return ''
    
    pbp_df['quarter_starter_names'] = pbp_df.apply(get_starter_names, axis=1)
    
    # Save to CSV
    pbp_df.to_csv('luka_first_game_with_quarters.csv', index=False)
    print(f"\n✅ Saved {len(pbp_df)} plays to luka_first_game_with_quarters.csv")
    
    # Also get the box score for verification
    print("\n" + "="*60)
    print("FETCHING BOX SCORE FOR VERIFICATION")
    print("="*60)
    
    boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=first_luka_game_id)
    player_stats = boxscore.player_stats.get_data_frame()
    
    # Find Luka in the box score
    luka_row = player_stats[player_stats['personId'] == 1629029]  # Luka's ID
    if len(luka_row) > 0:
        luka_pm = luka_row.iloc[0]['plusMinusPoints']
        print(f"Luka's plus/minus from box score: {luka_pm}")
    
    print("\n" + "="*60)
    print(f"Quarter starters detected:")
    for period, starters in quarter_starters.items():
        names = []
        for pid in starters:
            name_row = pbp_df[pbp_df['personId'] == pid].iloc[0] if len(pbp_df[pbp_df['personId'] == pid]) > 0 else None
            if name_row is not None:
                names.append(name_row['playerName'])
        print(f"  Q{period}: {', '.join(names)}")
    
    print("\n" + "="*60)
    print("NOW RUN testing.py TO CALCULATE LUKA'S PLUS/MINUS")
    print("="*60)
    
else:
    print("\n❌ No Luka games found!")