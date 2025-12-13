"""
Simple Web Monitor for Windows VPS
Shows bot status, recent trades, and system health
"""
import json
import psutil
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI(title="Forex Bot Monitor")

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
LOGS_DIR = PROJECT_DIR / "logs"


@app.get("/", response_class=HTMLResponse)
async def monitor_dashboard(request: Request):
    """Monitor dashboard"""
    
    # Get system stats
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    # Use project drive for disk usage
    project_drive = str(PROJECT_DIR.resolve())[:2] if str(PROJECT_DIR.resolve())[1] == ':' else '/'
    disk = psutil.disk_usage(project_drive)
    
    # Get trade log
    trade_log_file = DATA_DIR / "trade_log.json"
    trades = []
    if trade_log_file.exists():
        with open(trade_log_file) as f:
            trades = json.load(f)[-10:]  # Last 10 trades
    
    # Get last scrape info
    news_file = DATA_DIR / "all_news.json"
    last_scrape = "Never"
    news_count = 0
    if news_file.exists():
        with open(news_file) as f:
            news_data = json.load(f)
            last_scrape = news_data.get("scraped_at", "Unknown")
            news_count = news_data.get("count", 0)
    
    # Check MT5 connection
    mt5_status = "Unknown"
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            account = mt5.account_info()
            mt5_status = f"Connected - Balance: ${account.balance:,.2f}"
            mt5.shutdown()
        else:
            mt5_status = "Not Connected"
    except:
        mt5_status = "MT5 Not Available"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Forex Bot Monitor</title>
        <meta http-equiv="refresh" content="60">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Segoe UI', sans-serif; 
                background: linear-gradient(135deg, #1a1a2e, #16213e);
                color: #fff;
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1 {{ text-align: center; margin-bottom: 30px; color: #4da6ff; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .card {{
                background: rgba(255,255,255,0.05);
                border-radius: 10px;
                padding: 20px;
                border: 1px solid rgba(255,255,255,0.1);
            }}
            .card h2 {{ color: #4da6ff; margin-bottom: 15px; font-size: 1.2em; }}
            .stat {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }}
            .stat:last-child {{ border-bottom: none; }}
            .stat-value {{ font-weight: bold; }}
            .good {{ color: #4ade80; }}
            .warning {{ color: #fbbf24; }}
            .bad {{ color: #f87171; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
            th {{ color: #4da6ff; }}
            .buy {{ color: #4ade80; }}
            .sell {{ color: #f87171; }}
            .hold {{ color: #fbbf24; }}
            .timestamp {{ color: #888; font-size: 0.9em; text-align: center; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Forex Bot Monitor</h1>
            
            <div class="grid">
                <!-- System Status -->
                <div class="card">
                    <h2>💻 System Status</h2>
                    <div class="stat">
                        <span>CPU Usage</span>
                        <span class="stat-value {'good' if cpu_percent < 50 else 'warning' if cpu_percent < 80 else 'bad'}">{cpu_percent}%</span>
                    </div>
                    <div class="stat">
                        <span>Memory Usage</span>
                        <span class="stat-value {'good' if memory.percent < 50 else 'warning' if memory.percent < 80 else 'bad'}">{memory.percent}%</span>
                    </div>
                    <div class="stat">
                        <span>Disk Usage</span>
                        <span class="stat-value {'good' if disk.percent < 50 else 'warning' if disk.percent < 80 else 'bad'}">{disk.percent}%</span>
                    </div>
                </div>
                
                <!-- Bot Status -->
                <div class="card">
                    <h2>📊 Bot Status</h2>
                    <div class="stat">
                        <span>MetaTrader 5</span>
                        <span class="stat-value {'good' if 'Connected' in mt5_status else 'bad'}">{mt5_status}</span>
                    </div>
                    <div class="stat">
                        <span>Last Scrape</span>
                        <span class="stat-value">{last_scrape[:19] if len(last_scrape) > 19 else last_scrape}</span>
                    </div>
                    <div class="stat">
                        <span>News Articles</span>
                        <span class="stat-value">{news_count}</span>
                    </div>
                </div>
            </div>
            
            <!-- Recent Trades -->
            <div class="card" style="margin-top: 20px;">
                <h2>📈 Recent Trades</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Pair</th>
                            <th>Action</th>
                            <th>Lots</th>
                            <th>Confidence</th>
                            <th>SL/TP</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(f'''
                        <tr>
                            <td>{t.get("timestamp", "")[:16]}</td>
                            <td>{t.get("pair", "")}</td>
                            <td class="{t.get("action", "").lower()}">{t.get("action", "")}</td>
                            <td>{t.get("lots", 0)}</td>
                            <td>{t.get("confidence", 0)}%</td>
                            <td>{t.get("sl_pips", 0)}/{t.get("tp_pips", 0)}</td>
                        </tr>
                        ''' for t in reversed(trades)) if trades else '<tr><td colspan="6" style="text-align:center;">No trades yet</td></tr>'}
                    </tbody>
                </table>
            </div>
            
            <p class="timestamp">Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} (Auto-refresh every 60s)</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/api/status")
async def api_status():
    """API endpoint for status"""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
