"""
Forex Analysis Assistant - Main Entry Point
"""
import asyncio
import logging
import sys
from pathlib import Path

import uvicorn

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import HOST, PORT, LOG_LEVEL, DATA_DIR, LOGS_DIR
from web.app import app

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_DIR / "app.log", encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Run the application"""
    logger.info("Starting Forex Analysis Assistant...")
    logger.info(f"Server running at http://{HOST}:{PORT}")
    
    uvicorn.run(
        "web.app:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()
