# BLARE Strategy Template
# Copy this file, rename it to your strategy name, fill it in.
# Filename becomes the strategy ID — use snake_case, no spaces.
# Example: smc_fvg_liquidity_sweep.txt

# ============================================================
# STRATEGY METADATA
# ============================================================

STRATEGY_NAME: 
# Full human-readable name
# Example: SMC Liquidity Sweep + FVG Entry

STRATEGY_ID: 
# Must match filename without .txt extension
# Example: smc_fvg_liquidity_sweep

VERSION: 1.0
AUTHOR: Ovi
SOURCE: 
# Where this came from — YouTube channel, video title, timestamp
# Example: "ICT Mentorship 2022 — Core Concepts, 23:14"

MARKET: 
# Which markets this strategy applies to
# Options: crypto | forex | indices | commodities | all
# Example: crypto, forex

TIMEFRAMES:
# List all timeframes involved
# HTF = higher timeframe for bias
# MTF = mid timeframe for pattern formation  
# LTF = entry timeframe
HTF: 
MTF: 
LTF: 
# Example:
# HTF: 1D
# MTF: 4H
# LTF: 15m

DIRECTION: 
# Options: long | short | both
# Example: both


# ============================================================
# CORE CONCEPT
# ============================================================

CONCEPT:
# 2-4 sentences explaining WHY this setup works.
# What is the market doing? Who is being trapped?
# What is the underlying logic the trader explained?
#
# Example:
# "Smart money engineers liquidity by running stops above previous
# highs or below previous lows. Once they've collected the liquidity,
# they reverse price and leave a Fair Value Gap as evidence of their 
# entry. We enter when price returns to fill that FVG."


# ============================================================
# CONDITIONS — ALL MUST BE TRUE
# ============================================================
# List every condition that must be true before looking for entry.
# Be PRECISE. Include candle behavior, price levels, structure.

CONDITION_1: 
CONDITION_2: 
CONDITION_3: 
CONDITION_4: 
CONDITION_5: 

# Example:
# CONDITION_1: HTF (1D) trend is bullish — price above 20 EMA on daily
# CONDITION_2: Previous session high or swing high identified on MTF (4H)
# CONDITION_3: Price sweeps above that high by at least 0.1% (liquidity taken)
# CONDITION_4: Price closes back BELOW the swept high on MTF candle
# CONDITION_5: A Fair Value Gap (FVG) is present on LTF (15m) below current price


# ============================================================
# ENTRY TRIGGER
# ============================================================
# The EXACT moment to enter. What specific candle/price action confirms?

ENTRY_TRIGGER:
# Example:
# "Price retraces into the 15m FVG zone. Wait for a 15m candle to close
# bullish INSIDE or AT the bottom of the FVG. Enter on the open of the
# next candle after that bullish close."

ENTRY_TYPE: 
# Options: market | limit | stop_limit
# Example: limit


# ============================================================
# STOP LOSS
# ============================================================

STOP_PLACEMENT:
# Exact rule for stop loss placement.
# Example:
# "Below the lowest wick of the liquidity sweep candle, plus 0.1% buffer."

STOP_TYPE: 
# Options: fixed_pips | fixed_pct | structure_based
# Example: structure_based


# ============================================================
# TAKE PROFIT / TARGET
# ============================================================

TARGET_1:
# First target — partial profits
# Example: "Previous high that was swept. Close 50% of position here."

TARGET_2:
# Second target — runner
# Example: "Next HTF resistance / liquidity level above."

TARGET_TYPE:
# Options: fixed_rr | structure_level | liquidity_level
# Example: structure_level

MINIMUM_RR: 
# Minimum risk:reward to take the trade
# Example: 2.0


# ============================================================
# INVALIDATION
# ============================================================
# What cancels this trade idea entirely?

INVALIDATION_1: 
INVALIDATION_2: 
INVALIDATION_3: 

# Example:
# INVALIDATION_1: Price closes a 4H candle below the key swing low before entry
# INVALIDATION_2: HTF trend changes — daily closes below 20 EMA
# INVALIDATION_3: FVG is fully filled without a bullish reaction


# ============================================================
# FILTERS — AVOID THESE CONDITIONS
# ============================================================

AVOID_1: 
AVOID_2: 
AVOID_3: 

# Example:
# AVOID_1: Major news event within 30 minutes of entry
# AVOID_2: Price is in a choppy range (no clear structure) on HTF
# AVOID_3: Spread is unusually high (forex — avoid London open first 5 min)


# ============================================================
# PATTERN DETECTION RULES
# ============================================================
# Technical rules the pattern engine uses to detect this setup.
# Written in plain English but must be precise enough to code.

DETECT_STEP_1: 
DETECT_STEP_2: 
DETECT_STEP_3: 
DETECT_STEP_4: 
DETECT_STEP_5: 

# Example:
# DETECT_STEP_1: Identify the most recent swing high on MTF (highest high in last 20 candles)
# DETECT_STEP_2: Check if current candle high > swing high (sweep detected)
# DETECT_STEP_3: Check if current candle CLOSES below swing high (close-back confirmed)
# DETECT_STEP_4: Look back at last 5 LTF candles for a gap (FVG = candle where low > prev candle high, or high < prev candle low)
# DETECT_STEP_5: Mark FVG zone upper and lower bounds for entry limit order


# ============================================================
# EXAMPLES FROM SOURCE
# ============================================================
# Specific examples the trader walked through in the video.
# Helps understand edge cases and nuances.

EXAMPLE_1:
EXAMPLE_2:

# ============================================================
# KEY QUOTES FROM SOURCE
# ============================================================
# Direct quotes that capture the core logic best.

QUOTE_1: ""
QUOTE_2: ""
QUOTE_3: ""


# ============================================================
# NOTES
# ============================================================
# Anything else worth remembering about this strategy.
# Edge cases, market-specific behavior, personal observations.

NOTES:


# ============================================================
# BACKTEST RESULTS (fill in after testing)
# ============================================================

BACKTEST_MARKET: 
BACKTEST_PERIOD: 
BACKTEST_TRADES: 
BACKTEST_WIN_RATE: 
BACKTEST_AVG_RR: 
BACKTEST_MAX_DRAWDOWN: 
BACKTEST_NOTES:
