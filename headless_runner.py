import os
import sys
import logging
import traceback
from datetime import datetime

# Configure logging to catch all exceptions for GitHub Actions
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Headless Automated Execution - Gen-26 Financial Manager v3.0")
    
    # Check if we are running in a CI environment
    is_ci = os.getenv("GITHUB_ACTIONS") == "true"
    if is_ci:
        logger.info("Running in GitHub Actions environment.")
    
    try:
        # Import core modules
        logger.info("Importing engine modules...")
        import app
        import daily_paper_trade_logger
        import telemetry_tracker
        
        # 1. Run Data Fetch & Prediction Engine Snapshot
        logger.info("Executing run_engine_pipeline() for snapshots and predictions...")
        processed_data, df_rank = app.run_engine_pipeline()
        if processed_data and not df_rank.empty:
            logger.info("Engine Pipeline completed successfully. Snapshot generated.")
        else:
            logger.warning("Engine Pipeline returned empty or encountered a data fetch issue (e.g., weekend/offline).")

        # 2. Run Daily Paper Trade Logging
        logger.info("Executing run_daily_paper_trading() for execution journal updates...")
        try:
            # We assume run_daily_paper_trading updates the JSON/CSV directly.
            daily_paper_trade_logger.run_daily_paper_trading()
            logger.info("Paper trading journal updated successfully.")
        except Exception as e:
            logger.error(f"Error during paper trade logging: {e}")
            logger.error(traceback.format_exc())

        # 3. Update Model Drift & Calibration Telemetry
        logger.info("Executing telemetry_tracker for drift monitoring...")
        try:
            telemetry_tracker.compute_model_drift()
            logger.info("Telemetry and drift tracking updated successfully.")
        except Exception as e:
            logger.error(f"Error during telemetry tracking: {e}")
            logger.error(traceback.format_exc())

        logger.info("✅ Headless Automated Execution Completed Successfully.")

    except Exception as e:
        logger.critical("🚨 CRITICAL FAILURE IN HEADLESS RUNNER 🚨")
        logger.critical(str(e))
        logger.critical(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
