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

# Find ALL games with Luka
games_to_fetch = []
games_to_check = post_trade_games['GAME_ID'].tolist()

print("\nFinding all games with Luka...")
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

if games_to_fetch:
    print("\n" + "="*60)
    print("FETCHING PLAY-BY-PLAY AND DETECTING QUARTER STARTERS")
    print("="*60)
    
    all_plays = []
    all_starters = []
    all_box_scores = []
    
    for game_num, game_id in enumerate(games_to_fetch, 1):
        print(f"\n  Processing game {game_num}/{len(games_to_fetch)}: {game_id}")
        
        try:
            # Get play-by-play
            pbp = playbyplayv3.PlayByPlayV3(game_id=game_id)
            pbp_df = pbp.get_data_frames()[0]
            pbp_df['GAME_ID'] = game_id
            
            # Sort by period and action
            pbp_df = pbp_df.sort_values(['period', 'actionNumber'])
            
            # DETECT STARTERS FOR EACH QUARTER
            quarter_starters = {}
            current_period = 1
            players_seen = set()
            
            for idx, action in pbp_df.iterrows():
                period = action['period']
                team = action['teamTricode']
                player_id = action['personId']
                
                # If period changed, reset for new quarter
                if period != current_period:
                    current_period = period
                    players_seen = set()
                
                # If it's a LAL player and we haven't seen them yet
                if team == 'LAL' and player_id != 0 and player_id not in players_seen:
                    players_seen.add(player_id)
                    
                    # If we have 5 players, we found the starters for this quarter
                    if len(players_seen) == 5:
                        quarter_starters[period] = list(players_seen)
            
            # Add quarter starters info to the dataframe
            def get_quarter_starters(row):
                period = row['period']
                if period in quarter_starters:
                    return str(quarter_starters[period])
                return ''
            
            pbp_df['quarter_starters'] = pbp_df.apply(get_quarter_starters, axis=1)
            
            # Add to all plays
            all_plays.append(pbp_df)
            
            # Store starters for this game
            for period, starters in quarter_starters.items():
                all_starters.append({
                    'GAME_ID': game_id,
                    'period': period,
                    'starter_ids': str(starters)
                })
            
            # Get box score for verification
            boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
            player_stats = boxscore.player_stats.get_data_frame()
            
            # Find Luka's plus/minus
            luka_row = player_stats[player_stats['personId'] == 1629029]
            if len(luka_row) > 0:
                luka_pm = luka_row.iloc[0]['plusMinusPoints']
                all_box_scores.append({
                    'GAME_ID': game_id,
                    'luka_plus_minus': luka_pm
                })
                print(f"    ✅ {len(pbp_df)} plays, Box score +/-: {luka_pm}")
            else:
                print(f"    ✅ {len(pbp_df)} plays")
            
            time.sleep(0.3)
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    # Combine all games into one CSV
    if all_plays:
        full_df = pd.concat(all_plays, ignore_index=True)
        full_df.to_csv('luka_all_games_complete.csv', index=False)
        print(f"\n✅ Total plays across all games: {len(full_df)}")
        print("✅ Saved to luka_all_games_complete.csv")
        
        # Save all quarter starters
        if all_starters:
            starter_df = pd.DataFrame(all_starters)
            starter_df.to_csv('all_games_quarter_starters.csv', index=False)
            print("✅ Quarter starters saved to all_games_quarter_starters.csv")
        
        # Save box score plus/minus for verification
        if all_box_scores:
            box_df = pd.DataFrame(all_box_scores)
            box_df.to_csv('box_score_plus_minus.csv', index=False)
            print("✅ Box score plus/minus saved to box_score_plus_minus.csv")
        
        # Print summary
        print("\n" + "="*60)
        print("BOX SCORE PLUS/MINUS FOR VERIFICATION")
        print("="*60)
        for row in all_box_scores:
            print(f"  Game {row['GAME_ID']}: Luka +/- = {row['luka_plus_minus']}")
        
        print("\n" + "="*60)
        print("NOW RUN testing.py TO CALCULATE LUKA'S PLUS/MINUS")
        print("="*60)
        
    else:
        print("\n❌ No data fetched!")
else:
    print("\n❌ No Luka games found!")