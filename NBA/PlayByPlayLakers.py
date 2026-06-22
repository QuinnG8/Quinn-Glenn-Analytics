from nba_api.stats.endpoints import leaguegamefinder, playbyplayv3, boxscoretraditionalv3
from nba_api.stats.static import teams
import pandas as pd
import time
from collections import defaultdict

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

# Fetch only games that have Luka
games_to_fetch = []
games_to_check = post_trade_games['GAME_ID'].tolist()

print("\nIdentifying games with Luka (Dončić)...")
for idx, game_id in enumerate(games_to_check, 1):
    print(f"  Checking game {idx}/{len(games_to_check)}: {game_id}", end='')
    
    try:
        pbp = playbyplayv3.PlayByPlayV3(game_id=game_id)
        pbp_df = pbp.get_data_frames()[0]
        
        # Check for "Dončić" or "Doncic" in player names
        has_luka = pbp_df['playerName'].str.contains('Dončić|Doncic', case=False, na=False).any()
        
        if has_luka:
            print(f" ✓ Luka found!")
            games_to_fetch.append(game_id)
        else:
            print(f" - No Luka")
            
        time.sleep(0.3)
        
    except Exception as e:
        print(f" ✗ Error: {e}")

print(f"\n✅ Found Luka in {len(games_to_fetch)} games")
print(f"Game IDs: {games_to_fetch}")

if games_to_fetch:
    print("\n" + "="*60)
    print("FETCHING BOX SCORES FOR STARTING LINEUPS")
    print("="*60)
    
    starting_lineups = {}
    
    for idx, game_id in enumerate(games_to_fetch, 1):
        print(f"  Fetching box score {idx}/{len(games_to_fetch)}: {game_id}", end='')
        
        try:
            boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
            
            # Get player stats
            player_stats = boxscore.player_stats.get_data_frame()
            
            # Filter for Lakers players
            lakers_players = player_stats[player_stats['teamTricode'] == 'LAL']
            
            # The first 5 Lakers players in the box score are the starters
            # (the box score returns starters first, then bench players)
            starters = lakers_players.head(5)
            
            # Get the player IDs and names
            starter_ids = starters['personId'].tolist()
            starter_names = starters['firstName'] + ' ' + starters['familyName']
            
            starting_lineups[game_id] = {
                'ids': starter_ids,
                'names': starter_names.tolist()
            }
            
            print(f" ✓ {len(starter_ids)} starters found: {', '.join(starter_names.tolist())}")
            time.sleep(0.3)
            
        except Exception as e:
            print(f" ✗ Error: {e}")
    
    # Save starting lineups to a CSV
    if starting_lineups:
        lineup_df = pd.DataFrame([
            {
                'GAME_ID': game_id, 
                'starter_ids': str(data['ids']),
                'starter_names': ', '.join(data['names'])
            } 
            for game_id, data in starting_lineups.items()
        ])
        lineup_df.to_csv('lakers_starting_lineups.csv', index=False)
        print(f"\n✅ Starting lineups saved to lakers_starting_lineups.csv")
        
        # Print summary
        print("\n" + "="*60)
        print("STARTING LINEUPS SUMMARY (FIRST 5 GAMES)")
        print("="*60)
        for game_id, data in list(starting_lineups.items())[:5]:
            print(f"\nGame: {game_id}")
            print(f"  Starters: {', '.join(data['names'])}")
    
    print("\n" + "="*60)
    print("FETCHING PLAY-BY-PLAY FOR LUKA'S GAMES")
    print("="*60)
    
    all_plays = []
    
    for idx, game_id in enumerate(games_to_fetch, 1):
        print(f"  Fetching game {idx}/{len(games_to_fetch)}: {game_id}", end='')
        
        try:
            pbp = playbyplayv3.PlayByPlayV3(game_id=game_id)
            pbp_df = pbp.get_data_frames()[0]
            pbp_df['GAME_ID'] = game_id
            
            # Add starting lineup info to each row
            if game_id in starting_lineups:
                pbp_df['starters'] = str(starting_lineups[game_id]['ids'])
            
            all_plays.append(pbp_df)
            print(f" ✓ {len(pbp_df)} plays")
            time.sleep(0.3)
        except Exception as e:
            print(f" ✗ Error: {e}")
    
    if all_plays:
        full_df = pd.concat(all_plays, ignore_index=True)
        print(f"\n✅ Total plays: {len(full_df)}")
        full_df.to_csv('lakers_with_luka_complete.csv', index=False)
        print("✅ Saved to lakers_with_luka_complete.csv")
        
        # Also save the starting lineups separately for easy access
        print("\n✅ Starting lineups also saved to lakers_starting_lineups.csv")
    else:
        print("\n❌ No data was fetched!")