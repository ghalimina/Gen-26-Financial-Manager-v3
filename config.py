# config.py

class Config:
    # Portfolio & Risk Limits
    MAX_TOTAL_ALLOCATION_PCT = 0.65
    MAX_SINGLE_STOCK_ALLOCATION_PCT = 0.20
    
    # Transaction Costs
    TRANSACTION_COSTS_ROUND_TRIP = 0.0090  # 0.90%
    SLIPPAGE_ASSUMPTION = 0.0010  # 0.10%

    # Paper Trading
    PAPER_MIN_DAYS = 30
    
    # ML Settings
    ML_MODE = "CONFIDENCE_ONLY"  # Options: OFF, SHADOW, CONFIDENCE_ONLY, ACTIVE
    
    # Exit Rules
    STOP_RULE_TYPE = "ATR"
    TARGET_RULE_TYPE = "FIXED_RR"
    
    # Target and Risk Reward
    DEFAULT_RISK_REWARD_RATIO = 2.0
    
    # T+2 Settlement
    SETTLEMENT_DAYS = 2

    # Data Quality
    ALLOW_STALE_DATA_MINUTES = 15
    REQUIRE_FUNDAMENTALS = True

config = Config()
