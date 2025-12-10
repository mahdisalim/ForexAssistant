"""
Windows Service for Forex Analysis Assistant
Runs the trading bot as a Windows service using NSSM or pywin32

Usage:
    Install: python windows_service.py install
    Start: python windows_service.py start
    Stop: python windows_service.py stop
    Remove: python windows_service.py remove
"""
import sys
import os
import time
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    HAS_PYWIN32 = True
except ImportError:
    HAS_PYWIN32 = False
    print("pywin32 not installed. Install with: pip install pywin32")

# Setup logging
LOG_FILE = Path(__file__).parent.parent / "logs" / "service.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ForexService")


if HAS_PYWIN32:
    class ForexAssistantService(win32serviceutil.ServiceFramework):
        """Windows Service for Forex Trading Bot"""
        
        _svc_name_ = "ForexAssistant"
        _svc_display_name_ = "Forex Analysis Assistant"
        _svc_description_ = "AI-powered forex market analysis and trading bot"
        
        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self.running = True
        
        def SvcStop(self):
            """Stop the service"""
            logger.info("Service stop requested")
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.stop_event)
            self.running = False
        
        def SvcDoRun(self):
            """Run the service"""
            logger.info("Service starting...")
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            self.main()
        
        def main(self):
            """Main service loop"""
            import asyncio
            from trading_bot import TradingBot
            from dotenv import load_dotenv
            
            load_dotenv()
            
            bot = TradingBot(
                mt5_login=int(os.getenv("MT5_LOGIN", 0)),
                mt5_password=os.getenv("MT5_PASSWORD", ""),
                mt5_server=os.getenv("MT5_SERVER", ""),
                account_balance=float(os.getenv("ACCOUNT_BALANCE", 10000)),
                risk_percent=float(os.getenv("RISK_PERCENT", 1.0)),
                min_confidence=int(os.getenv("MIN_CONFIDENCE", 60)),
                demo_mode=os.getenv("DEMO_MODE", "true").lower() == "true"
            )
            
            # Run bot with periodic check for stop signal
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                while self.running:
                    # Run one trading cycle
                    loop.run_until_complete(bot._trading_cycle())
                    
                    # Wait 5 minutes or until stop signal
                    result = win32event.WaitForSingleObject(self.stop_event, 300000)
                    if result == win32event.WAIT_OBJECT_0:
                        break
            except Exception as e:
                logger.error(f"Service error: {e}")
            finally:
                loop.close()
                logger.info("Service stopped")


def install_with_nssm():
    """Alternative: Install using NSSM (Non-Sucking Service Manager)"""
    import subprocess
    
    project_path = Path(__file__).parent.parent
    python_exe = sys.executable
    script_path = project_path / "trading_bot.py"
    
    print("Installing with NSSM...")
    print(f"Python: {python_exe}")
    print(f"Script: {script_path}")
    
    # Download NSSM if not present
    nssm_path = project_path / "deploy" / "nssm.exe"
    if not nssm_path.exists():
        print("Please download NSSM from https://nssm.cc/download")
        print(f"And place nssm.exe in: {nssm_path.parent}")
        return
    
    # Install service
    subprocess.run([
        str(nssm_path), "install", "ForexAssistant",
        python_exe, str(script_path)
    ])
    
    # Set working directory
    subprocess.run([
        str(nssm_path), "set", "ForexAssistant",
        "AppDirectory", str(project_path)
    ])
    
    # Set description
    subprocess.run([
        str(nssm_path), "set", "ForexAssistant",
        "Description", "AI-powered forex market analysis and trading bot"
    ])
    
    print("Service installed! Start with: nssm start ForexAssistant")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'nssm':
        install_with_nssm()
    elif HAS_PYWIN32:
        win32serviceutil.HandleCommandLine(ForexAssistantService)
    else:
        print("Usage:")
        print("  With pywin32: python windows_service.py [install|start|stop|remove]")
        print("  With NSSM:    python windows_service.py nssm")
