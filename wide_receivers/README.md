# NFL Draft Analytics: Wide Receivers (2017-2025)

**Speed gets you drafted. YAC above expected makes you a star.**

This repository analyzes what actually predicts NFL success for wide receivers. I combined college production, combine athletic testing, draft capital, and NFL outcomes to answer one question: *Which pre-draft metrics separate stars from busts?*

---

## The Short Answer

| What matters | What doesn't |
|--------------|---------------|
| College touchdowns (≥12 = elite upside) | 40-yard dash (predicts draft slot, not success) |
| Yards per catch (deep threat ability translates) | College yards per game (volume alone means nothing) |
| YAC above expected (the #1 separator of NFL tiers) | 3-cone drill (teams overvalue it) |
| Draft capital (top-100 picks succeed at 89%) | Broad jump (explosiveness ≠ production) |

**The takeaway:** NFL teams draft on speed and conference pedigree. But once players are in the league, YAC above expected separates the elites from the busts. And the best pre-draft predictors of YAC ability? College touchdowns and yards per catch.

---

## Notebooks

| Notebook | Question | Key Finding |
|----------|----------|-------------|
| [01_draft_hit_rate](01_draft_hit_rate.html) | Where should teams draft WRs? | Round 2 offers the best value (78% become starters). After Round 3, bust rates exceed 70%. |
| [02_college_ypg_analysis](02_college_ypg_analysis.html) | Does college production drive draft position? | Elite producers (90+ YPG) appear in every round. Production alone doesn't explain draft slot. |
| [03_combine_scatter](03_combine_scatter.html) | What actually drives draft position? | 40-yard dash (r=0.38) correlates more with draft position than any college metric. |
| [04_predictive_NFL_success](04_predictive_NFL_success.html) | What predicts NFL success? | YAC above expected separates Elite (1.10) from Bust (0.33). College TDs and Y/R matter more than combine drills. |

---

## Data Sources

- **College stats:** Yards per game, yards per catch, peak touchdowns, conference
- **Combine results:** 40-yard dash, 3-cone drill, broad jump, vertical, bench
- **NFL outcomes:** NextGen Stats (cushion, separation, YAC above expected), draft position
- **Years covered:** 2017-2025 draft classes

---

## Key Visualizations

The most important chart in this analysis is the scatter plot from Notebook 03:

[![WR Draft Scatter](wr_draft_scatter_by_pick.png)](03_combine_scatter.html)

It shows three things at once:
- **X-axis:** 40-yard dash time (faster = further right on inverted axis)
- **Y-axis:** Draft position (earlier = higher)
- **Size:** College YPG (bigger circles = more productive)
- **Color:** Conference (red = SEC/Big Ten, blue = other Power 5, green = other)

The pattern is clear: faster players get drafted earlier, regardless of college production.

---

## Limitations

This analysis has real constraints. Read the full "Where This Analysis Falls Short" section in Notebook 04, but here's the summary:

- **Small YAC sample:** Only 112 of 292 players had NextGen Stats data
- **No external validation:** Tier definitions weren't cross-referenced against PFF or Pro Bowls
- **Missing variables:** No injury history, age at draft, or target share data
- **No position subgroups:** Slot and boundary receivers analyzed together
- **Draft capital bias:** Can't distinguish talent from opportunity

These don't invalidate the findings. They just mean this is a portfolio project, not a peer-reviewed study.

---

## What's Next

This repository currently covers **wide receivers only**. Future work could include:

- Defensive linemen (in progress)
- Team-specific draft analysis (e.g., how the 49ers draft at each position)

---

## About the Author

I'm a computer science graduate who loves to tell stories. Whether that be through data, visualizations, or simply words, I love to learn and and share what I've learned. This is my portfolio project for data analyst roles. If you're hiring, I'd love to talk.
