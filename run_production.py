#!/usr/bin/env python3
"""
Production deployment script for signal detection plugin
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import SignalDetectionPlugin


class ProductionRunner:
    """Production runner for the signal detection plugin"""
    
    def __init__(self):
        self.plugin = None
        self.running = False
        
    async def start(self):
        """Start the plugin in production mode"""
        try:
            # Configure logging for production
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('signal_detection.log'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            logger = logging.getLogger(__name__)
            logger.info("Starting Signal Detection Plugin in production mode")
            
            # Initialize plugin
            config_path = str(Path(__file__).parent / "config.yaml")
            self.plugin = SignalDetectionPlugin(config_path)
            await self.plugin.initialize()
            
            # Set up signal handlers for graceful shutdown
            self.setup_signal_handlers()
            
            # Start plugin
            logger.info("Plugin initialized successfully")
            self.running = True
            
            # Run until stopped
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logging.error(f"Failed to start plugin: {e}")
            raise
            
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logging.info(f"Received signal {signum}, shutting down gracefully...")
            asyncio.create_task(self.shutdown())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def shutdown(self):
        """Graceful shutdown"""
        self.running = False
        if self.plugin:
            await self.plugin.shutdown()
        logging.info("Signal Detection Plugin stopped")


async def main():
    """Main entry point"""
    runner = ProductionRunner()
    try:
        await runner.start()
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
