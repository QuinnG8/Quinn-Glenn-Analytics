from nba_api.stats.endpoints import leaguegamefinder, playbyplayv3, boxscoretraditionalv3
from nba_api.stats.static import teams
import pandas as pd
import time

# Fine Lakers Team ID
lakers = teams.find_team_by_abbreviation('LAL')
lakers_id = lakers['id']
time.sleep(1.0)

print(f"Lakers Team ID: {lakers_id}")

# Get Lakers games for 2024-2025
season = '2024-25'
gamefinder = leaguegamefinder.LeagueGameFinder(
    team_id_nullable=lakers_id,
    season_nullable=season
)

games_df = gamefinder.get_data_frames()[0]
regular_season = games_df[games_df['GAME_ID'].str.startswith('002')]

# Post Luka trade games
regular_season = regular_season.copy()
regular_season['GAME_DATE'] = pd.to_datetime(regular_season['GAME_DATE'])
post_trade_games = regular_season[regular_season['GAME_DATE'] >= '2025-02-01']

# Finding games with Luka
games_to_fetch = []
games_to_check = post_trade_games['GAME_ID'].tolist()

print("\nFinding all games with Luka...")
for idx, game_id in enumerate(games_to_check, 1):
    print(f"  Checking game {idx}/{len(games_to_check)}: {game_id}", end='') 

    boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
    player_stats = boxscore.player_stats.get_data_frame()

    has_luka = (player_stats['personId'] == 1629029).any()    
        
    if has_luka:
        print(f"✓")
        games_to_fetch.append(game_id)
    else:
        print(f"✗")

    time.sleep(0.3)
            
print(f"\n✅ Found Luka in {len(games_to_fetch)} games")
    

if games_to_fetch:
    all_plays = []
    all_starters = []
    all_box_scores = []

    for game_num, game_id in enumerate(games_to_fetch, 1):
        print(f"\n Processing game {game_num}/{len(games_to_fetch)}: {game_id}")

        pbp = playbyplayv3.PlayByPlayV3(game_id=game_id)
        pbp_df = pbp.get_data_frames()[0]

        pbp_df['GAME_ID'] = game_id

        pbp_df = pbp_df.sort_values(['period', 'actionNumber'])

        # Find starters for each quarter
        quarer_starters = {}
        current_period = 1
        players_seen = set()

        