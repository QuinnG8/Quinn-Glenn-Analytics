from nba_api.stats.endpoints import leaguegamefinder, playbyplayv3
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
    print("FETCHING PLAY-BY-PLAY FOR LUKA'S GAMES")
    print("="*60)
    
    all_plays = []
    
    for idx, game_id in enumerate(games_to_fetch, 1):
        print(f"  Fetching game {idx}/{len(games_to_fetch)}: {game_id}", end='')
        
        try:
            pbp = playbyplayv3.PlayByPlayV3(game_id=game_id)
            pbp_df = pbp.get_data_frames()[0]
            pbp_df['GAME_ID'] = game_id
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
        
        # Now run the lineup analysis
        print("\n" + "="*60)
        print("RUNNING LINEUP ANALYSIS")
        print("="*60)
        
        # Find Luka's ID
        luka_rows = full_df[full_df['playerName'].str.contains('Dončić|Doncic', case=False, na=False)]
        if len(luka_rows) > 0:
            luka_id = luka_rows.iloc[0]['personId']
            print(f"Luka's personId: {luka_id}")
            print(f"Luka's name in data: {luka_rows.iloc[0]['playerName']}")
        
        # Track lineups
        luka_lineups = defaultdict(lambda: {'possessions': 0, 'points_for': 0, 'points_against': 0})
        
        for game_id in games_to_fetch:
            game_df = full_df[full_df['GAME_ID'] == game_id].copy()
            game_df = game_df.sort_values(['period', 'actionNumber'])
            
            home_on_court = set()
            away_on_court = set()
            luka_on_court = False
            
            last_score_home = 0
            last_score_away = 0
            
            for idx, action in game_df.iterrows():
                action_type = action['actionType']
                player_id = action['personId']
                team = action['teamTricode']
                score_home = action['scoreHome'] if pd.notna(action['scoreHome']) else last_score_home
                score_away = action['scoreAway'] if pd.notna(action['scoreAway']) else last_score_away
                
                # Handle substitutions
                if action_type == 'substitution':
                    if team == 'LAL':
                        if player_id in home_on_court:
                            home_on_court.remove(player_id)
                        else:
                            home_on_court.add(player_id)
                    else:
                        if player_id in away_on_court:
                            away_on_court.remove(player_id)
                        else:
                            away_on_court.add(player_id)
                
                # Check if Luka is on court (by ID or name)
                if player_id == luka_id or action['playerName'] == 'Dončić':
                    luka_on_court = True
                
                # If Luka is on court, record the lineup and score change
                if luka_on_court and action_type not in ['substitution', 'timeout', 'period']:
                    lakers_lineup = tuple(sorted([p for p in home_on_court if p != luka_id]))
                    
                    if lakers_lineup:
                        points_for_lakers = score_home - last_score_home
                        points_against_lakers = score_away - last_score_away
                        
                        if points_for_lakers != 0 or points_against_lakers != 0:
                            luka_lineups[lakers_lineup]['possessions'] += 1
                            luka_lineups[lakers_lineup]['points_for'] += points_for_lakers
                            luka_lineups[lakers_lineup]['points_against'] += points_against_lakers
                
                last_score_home = score_home
                last_score_away = score_away
        
        # Helper function to get player names
        def get_player_name(player_id):
            if player_id == luka_id:
                return 'Luka Dončić'
            name_rows = full_df[full_df['personId'] == player_id]
            if len(name_rows) > 0:
                return name_rows.iloc[0]['playerName']
            return str(player_id)
        
        # Convert to DataFrame
        lineup_results = []
        for lineup, stats in luka_lineups.items():
            if stats['possessions'] > 0:
                # Get player names (excluding Luka)
                player_names = []
                for p in lineup:
                    if p != luka_id:
                        name = get_player_name(p)
                        if name and name != '':
                            player_names.append(name)
                
                lineup_results.append({
                    'lineup_players': lineup,
                    'player_names': ', '.join(player_names),
                    'possessions': stats['possessions'],
                    'points_for': stats['points_for'],
                    'points_against': stats['points_against'],
                    'plus_minus': stats['points_for'] - stats['points_against'],
                    'net_rating': (stats['points_for'] - stats['points_against']) / stats['possessions'] * 100 if stats['possessions'] > 0 else 0
                })
        
        results_df = pd.DataFrame(lineup_results)
        if len(results_df) > 0:
            results_df = results_df.sort_values('plus_minus', ascending=False)
            print("\n" + "="*60)
            print("TOP LINEUPS WITH LUKA (by plus/minus)")
            print("="*60)
            print(results_df[['player_names', 'possessions', 'points_for', 'points_against', 'plus_minus', 'net_rating']].head(10))
            
            results_df.to_csv('luka_lineup_analysis_complete.csv', index=False)
            print("\n✅ Results saved to luka_lineup_analysis_complete.csv")
        else:
            print("\nNo lineup data found")
else:
    print("\n❌ No games found with Luka")