import pandas as pd
from collections import defaultdict

print("="*60)
print("STEP 1: LOADING DATA")
print("="*60)

try:
    full_df = pd.read_csv('lakers_with_luka_complete.csv')
    print(f"Loaded {len(full_df)} plays from CSV")
except:
    print("CSV not found! Please run the fetch script first.")
    exit()

full_df['scoreHome'] = pd.to_numeric(full_df['scoreHome'], errors='coerce')
full_df['scoreAway'] = pd.to_numeric(full_df['scoreAway'], errors='coerce')

# Find Luka's ID
luka_rows = full_df[full_df['playerName'].str.contains('Dončić|Doncic', case=False, na=False)]
if len(luka_rows) > 0:
    luka_id = luka_rows.iloc[0]['personId']
    print(f"Luka's personId: {luka_id}")
else:
    print("Luka not found in data!")
    exit()

print("="*60)
print("STEP 2: LINEUP ANALYSIS")
print("="*60)

games = full_df['GAME_ID'].unique()
print(f"Processing {len(games)} games...")

luka_lineups = defaultdict(lambda: {
    'possessions': 0,
    'points_for': 0,
    'points_against': 0,
    'stints': 0
})

for game_id in games:
    game_df = full_df[full_df['GAME_ID'] == game_id].copy()
    game_df = game_df.sort_values(['period', 'actionNumber'])

    # Initialize starting lineup from first LAL players in period 1 before any sub
    period1 = game_df[game_df['period'] == 1]
    lal_starters = set()
    for _, row in period1.iterrows():
        if row['actionType'] == 'substitution':
            break
        if row['teamTricode'] == 'LAL' and pd.notna(row['personId']) and row['personId'] != 0:
            lal_starters.add(row['personId'])
        if len(lal_starters) >= 5:
            break

    home_players = set(lal_starters)
    current_home_score = 0
    current_away_score = 0
    stint_start_score_home = 0
    stint_start_score_away = 0
    stint_players = set()
    luka_possessions = 0  # real possession counter for current stint

    # Check if Luka starts
    luka_on_court = luka_id in home_players
    if luka_on_court:
        stint_players = set([p for p in home_players if p != luka_id])

    for _, action in game_df.iterrows():
        action_type = action['actionType']
        player_id = action['personId']
        team = action['teamTricode']

        # Update scores
        score_home = action['scoreHome'] if pd.notna(action['scoreHome']) else current_home_score
        score_away = action['scoreAway'] if pd.notna(action['scoreAway']) else current_away_score
        current_home_score = score_home
        current_away_score = score_away

        # Count real possessions while Luka is on court
        if luka_on_court:
            sub_type = str(action.get('subType', '')).lower()

            is_made_shot = action_type == 'Made Shot'
            is_turnover = action_type == 'Turnover'
            is_end_of_quarter = action_type == 'period' and sub_type == 'end'
            is_jump_ball = action_type == 'Jump Ball'

            if is_made_shot or is_turnover or is_end_of_quarter or is_jump_ball:
                luka_possessions += 1

        # Handle substitutions using subType (in/out)
        if action_type == 'substitution' and team == 'LAL':
            sub_type = str(action.get('subType', '')).lower()
            if sub_type == 'out':
                home_players.discard(player_id)
            elif sub_type == 'in':
                home_players.add(player_id)

        luka_was_on = luka_on_court
        luka_on_court = luka_id in home_players

        # Luka left the court — record the stint
        if luka_was_on and not luka_on_court:
            if len(stint_players) == 4:
                lineup_tuple = tuple(sorted(stint_players))
                points_scored = current_home_score - stint_start_score_home
                points_allowed = current_away_score - stint_start_score_away
                luka_lineups[lineup_tuple]['points_for'] += points_scored
                luka_lineups[lineup_tuple]['points_against'] += points_allowed
                luka_lineups[lineup_tuple]['possessions'] += luka_possessions
                luka_lineups[lineup_tuple]['stints'] += 1
            stint_players = set()
            luka_possessions = 0  # reset for next stint

        # Luka came on the court — start a new stint
        if not luka_was_on and luka_on_court:
            teammates = set([p for p in home_players if p != luka_id])
            if len(teammates) == 4:
                stint_players = teammates
                stint_start_score_home = current_home_score
                stint_start_score_away = current_away_score

    # End of game — record whatever stint Luka was in
    if luka_on_court and len(stint_players) == 4:
        lineup_tuple = tuple(sorted(stint_players))
        points_scored = current_home_score - stint_start_score_home
        points_allowed = current_away_score - stint_start_score_away
        luka_lineups[lineup_tuple]['points_for'] += points_scored
        luka_lineups[lineup_tuple]['points_against'] += points_allowed
        luka_lineups[lineup_tuple]['possessions'] += luka_possessions
        luka_lineups[lineup_tuple]['stints'] += 1


# Helper to look up player names
def get_player_name(player_id):
    if player_id == luka_id:
        return 'Luka Dončić'
    name_rows = full_df[full_df['personId'] == player_id]
    if len(name_rows) > 0:
        return name_rows.iloc[0]['playerName']
    return str(player_id)


# Build results
print("\nBuilding results...")
lineup_results = []

for lineup_tuple, stats in luka_lineups.items():
    if stats['stints'] > 0:
        player_names = []
        for p in lineup_tuple:
            name = get_player_name(p)
            if name and name != '' and 'Dončić' not in name and 'Doncic' not in name:
                player_names.append(name)

        if len(player_names) == 4:
            possessions = stats['possessions']
            points_for = stats['points_for']
            points_against = stats['points_against']
            plus_minus = points_for - points_against

            if possessions > 0:
                offensive_rating = round((points_for / possessions) * 100, 1)
                defensive_rating = round((points_against / possessions) * 100, 1)
                net_rating = round(offensive_rating - defensive_rating, 1)
            else:
                offensive_rating = defensive_rating = net_rating = 0

            lineup_results.append({
                'player_names': ', '.join(player_names),
                'stints': stats['stints'],
                'possessions': possessions,
                'points_for': points_for,
                'points_against': points_against,
                'plus_minus': plus_minus,
                'offensive_rating': offensive_rating,
                'defensive_rating': defensive_rating,
                'net_rating': net_rating
            })

print(f"\n✅ Valid lineups: {len(lineup_results)}")

if lineup_results:
    results_df = pd.DataFrame(lineup_results)

    total_possessions = results_df['possessions'].sum()
    total_points_for = results_df['points_for'].sum()
    total_points_against = results_df['points_against'].sum()
    total_plus_minus = total_points_for - total_points_against

    print(f"\n📊 TOTAL STATS ACROSS ALL LINEUPS:")
    print(f"   Total points FOR:     {total_points_for:.0f}")
    print(f"   Total points AGAINST: {total_points_against:.0f}")
    print(f"   Overall plus/minus:   {total_plus_minus:.0f}")
    print(f"   Total possessions:    {total_possessions}")

    luka_games = [
        gid for gid in games
        if full_df[full_df['GAME_ID'] == gid]['playerName'].str.contains('Dončić|Doncic', case=False, na=False).any()
    ]
    print(f"\n📊 VERIFICATION:")
    print(f"   Luka played in {len(luka_games)} games")
    print(f"   Possessions per game: {total_possessions / len(luka_games):.1f}")
    estimated_mpg = (total_possessions / len(luka_games) / 100) * 48
    print(f"   Estimated Luka MPG:   {estimated_mpg:.1f}")

    print("\n" + "="*60)
    print("MOST USED LINEUPS WITH LUKA (by possessions)")
    print("="*60)
    by_usage = results_df.sort_values('possessions', ascending=False)
    print(by_usage[['player_names', 'stints', 'possessions', 'points_for', 'points_against', 'plus_minus']].head(10).to_string(index=False))

    print("\n" + "="*60)
    print("BEST LINEUPS WITH LUKA (net rating, min 30 possessions)")
    print("="*60)
    filtered = results_df[results_df['possessions'] >= 30].sort_values('net_rating', ascending=False)
    if len(filtered) > 0:
        print(filtered[['player_names', 'possessions', 'points_for', 'points_against', 'plus_minus', 'net_rating']].head(10).to_string(index=False))
    else:
        print("No lineups with 30+ possessions yet.")

    results_df.to_csv('luka_lineup_analysis_final.csv', index=False)
    print("\n✅ Results saved to luka_lineup_analysis_final.csv")

else:
    print("\n❌ No valid lineups found!")

print("\n" + "="*60)
print("✅ DONE!")
print("="*60)