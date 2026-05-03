# Stardew Valley Skull Cavern Monte-Carlo Simulation
This is the final project for is597 Program Quality & Analytics 2026Spring.

# Overview
A Monte Carlo simulation of Stardew Valley's **Skull Cavern** that analyzes expected floor depth reached and net profit (ROI) per run as a function of player luck and strategy. The simulation is built on top of the 2022 Fall project's Mines simulator by reusing concrete assets (equipment/rock CSV schemas, `if_convergent()` validator) but introducing new core classes for Skull Cavern-specific mechanics: an in-game **time budget**, **ladder/shaft exit logic driven by luck**, **bomb-usage** strategy, **food-usage** strategy, and a reviving-Mummy combat mechanic.  
<img width="80%" alt="Skullkeyentrance" src="https://github.com/user-attachments/assets/9af58b64-3330-41f8-b00d-a90fe7e34757"/>


# Hypotheses
**H1 — Luck vs bomb effect on depth**  
Higher luck increases expected floor depth more than bomb usage.
Formally: the depth gain from moving from the lowest to the highest luck level (with bombs off) exceeds the depth gain from switching bombs on (with luck held neutral).

**H2 — Distributional dominance & quantile crossing**  
Bomb+food has higher expected profit but higher variance. - a risk-return tradeoff
Formally: The bomb+food strategy's net-profit distribution crosses the pickaxe+no-food distribution: bomb+food dominates in the upper quantile (deep successful runs) and is dominated in the lower quantile (early deaths where the upfront cost isn't recovered).

**H3 — Depth → profit correlation**  
Deeper floors reached correlate with higher net profit, because deeper floors have higher-value ore and monster drops. Pooled Pearson correlation should be large positive (r > 0.6).

# Phases
## Phase 1 - Random variables
- Ladder probability
- Shaft depth distribution
- Resource drop rates
- Monster spawn probability
- Player damage / survival

## Phase 2 - Controls & experiments
Player stats including:
- Luck level
- Mining skill level
- Bombs vs Pickaxe strategy
- Food vs No food
  
## Phase 3 - Analysis
- Expected floor reached
- Expected ores per run
- Survival probability
- Net profit for different strategy

# Appendix A. Simplifying Assumptions
1. Bombs and food are acquired by purchase (upfront cost) before the run; no mid-run purchases.
2. Combat is turn-based between one player and one monster at a time.
3. Equipment is held constant across all runs and hypotheses.
4. A run ends when the player dies or when the in-game time budget (1200 minutes = 20 in-game hours, 6 AM → 2 AM) is exhausted.
5. Every Skull Cavern run starts at floor 1 (no elevator in Skull Cavern).
6. Infested/Infection floors (monster-only, ladder appears after all monsters killed) are not simulated. Every floor has U{30,50} rocks and U{2,6} monsters.
7. If a floor is fully rock-cleared without an exit appearing probabilistically, the last rock is guaranteed to reveal a ladder.
8. Bomb clusters roll for exit once per bomb (not once per rock cleared in the cluster).
9. Only the regular `Bomb` type is simulated in the first pass (Cherry Bomb and Mega Bomb are ignored).
10. Food's luck buff is ignored; food is modeled purely as an HP-restore consumable.
11. Luck is a controlled input, taking one of 6 discrete values from wiki thresholds, not sampled from its natural daily distribution.
12. On death, the player retains 70% of accumulated revenue; the upfront cost is still paid in full.
13. Mummy revive: a Mummy killed by pickaxe has a 50% chance to revive once per floor. A Mummy killed while at least one bomb was used on that floor stays permanently dead.
14. Active-monster combat is rolled at 5% per rock broken on floors containing active-attack monsters.

# Data Sources
- [https://stardewvalleywiki.com/Skull_Cavern](https://stardewvalleywiki.com/Skull_Cavern)
- [https://stardewvalleywiki.com/Footwear](https://stardewvalleywiki.com/Footwear)
- [https://stardewvalleywiki.com/Weapons#Sword](https://stardewvalleywiki.com/Weapons#Sword)
