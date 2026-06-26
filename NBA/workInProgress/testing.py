from nba_api.stats.endpoints import playbyplayv3
import pandas as pd

GAME_ID = "0022401185"

pbp = playbyplayv3.PlayByPlayV3(
    game_id=GAME_ID,
    start_period=1,
    end_period=4  # use 10 if you want to include any possible OT periods
)

df = pbp.get_data_frames()[0]

df.to_csv("lakers_rockets_game81_playbyplay.csv", index=False)