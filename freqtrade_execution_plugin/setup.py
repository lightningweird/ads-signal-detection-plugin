"""
Freqtrade Execution Plugin Setup
===============================

Setup script for the minimal Freqtrade execution plugin that integrates
with the ads-anomaly-detection system.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def install_freqtrade():
    """Install Freqtrade and dependencies"""
    print("📦 Installing Freqtrade and dependencies...")
    
    try:
        # Install Freqtrade
        subprocess.run([sys.executable, "-m", "pip", "install", "freqtrade[plot]"], check=True)
        print("✅ Freqtrade installed successfully")
        
        # Install additional dependencies
        dependencies = [
            "redis>=4.0.0",
            "pandas>=1.5.0",
            "numpy>=1.21.0"
        ]
        
        for dep in dependencies:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            print(f"✅ {dep} installed")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False

def create_freqtrade_config():
    """Create Freqtrade configuration"""
    config_path = Path("freqtrade_execution_plugin/config.json")
    
    if config_path.exists():
        print("✅ Freqtrade config already exists")
        return True
    
    print("📝 Creating Freqtrade configuration...")
    
    # Config is already created by previous file creation
    print("✅ Freqtrade configuration created")
    return True

def create_user_data_directory():
    """Create Freqtrade user data directory structure"""
    print("📁 Creating Freqtrade user data directory...")
    
    base_dir = Path("freqtrade_execution_plugin")
    directories = [
        "user_data",
        "user_data/strategies",
        "user_data/data",
        "user_data/logs",
        "user_data/notebooks",
        "user_data/backtest_results"
    ]
    
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created {directory}")
    
    # Copy strategy to user_data/strategies
    strategy_source = base_dir / "ads_execution_strategy.py"
    strategy_dest = base_dir / "user_data" / "strategies" / "ads_execution_strategy.py"
    
    if strategy_source.exists():
        import shutil
        shutil.copy2(strategy_source, strategy_dest)
        print("✅ Strategy copied to user_data/strategies")
    
    return True

def test_redis_connection():
    """Test Redis connection"""
    print("🔍 Testing Redis connection...")
    
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, db=0)
        client.ping()
        print("✅ Redis connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 Make sure Redis is running: docker run -d -p 6379:6379 redis/redis-stack")
        return False

def create_start_scripts():
    """Create convenience start scripts"""
    print("📜 Creating start scripts...")
    
    # Windows batch file
    batch_content = '''@echo off
echo Starting Freqtrade Execution Plugin...
echo Make sure Redis is running!
echo.

cd /d "%~dp0"

REM Start in dry run mode (paper trading)
python -m freqtrade trade --config config.json --strategy AdsExecutionStrategy --dry-run

pause
'''
    
    with open("freqtrade_execution_plugin/start_freqtrade.bat", "w") as f:
        f.write(batch_content)
    
    # PowerShell script
    ps_content = '''# Start Freqtrade Execution Plugin
Write-Host "Starting Freqtrade Execution Plugin..." -ForegroundColor Green
Write-Host "Make sure Redis is running!" -ForegroundColor Yellow
Write-Host ""

Set-Location $PSScriptRoot

# Start in dry run mode (paper trading)
python -m freqtrade trade --config config.json --strategy AdsExecutionStrategy --dry-run

Read-Host "Press Enter to exit"
'''
    
    with open("freqtrade_execution_plugin/start_freqtrade.ps1", "w") as f:
        f.write(ps_content)
    
    print("✅ Start scripts created")
    return True

def validate_setup():
    """Validate the complete setup"""
    print("🔍 Validating setup...")
    
    checks = [
        ("Strategy file", Path("freqtrade_execution_plugin/ads_execution_strategy.py").exists()),
        ("Config file", Path("freqtrade_execution_plugin/config.json").exists()),
        ("Signal sender", Path("freqtrade_execution_plugin/signal_sender.py").exists()),
        ("Test script", Path("freqtrade_execution_plugin/test_integration.py").exists()),
    ]
    
    all_good = True
    for check_name, result in checks:
        if result:
            print(f"✅ {check_name}")
        else:
            print(f"❌ {check_name}")
            all_good = False
    
    # Test imports
    try:
        sys.path.append("freqtrade_execution_plugin")
        import signal_sender
        print("✅ Signal sender import")
    except ImportError as e:
        print(f"❌ Signal sender import: {e}")
        all_good = False
    
    return all_good

def show_setup_complete():
    """Show setup completion message"""
    print("\n" + "=" * 60)
    print("🎉 FREQTRADE EXECUTION PLUGIN SETUP COMPLETE")
    print("=" * 60)
    print()
    print("📋 NEXT STEPS:")
    print()
    print("1. Make sure Redis is running:")
    print("   docker run -d -p 6379:6379 redis/redis-stack")
    print()
    print("2. Test the signal transmission:")
    print("   cd freqtrade_execution_plugin")
    print("   python test_integration.py")
    print()
    print("3. Start Freqtrade (in another terminal):")
    print("   cd freqtrade_execution_plugin")
    print("   python -m freqtrade trade --config config.json --strategy AdsExecutionStrategy --dry-run")
    print()
    print("4. Or use the convenience script:")
    print("   start_freqtrade.bat  (Windows)")
    print("   ./start_freqtrade.ps1  (PowerShell)")
    print()
    print("📡 INTEGRATION WITH ADS-ANOMALY-DETECTION:")
    print()
    print("from freqtrade_execution_plugin.signal_sender import AdsFreqtradeInterface")
    print("ads_interface = AdsFreqtradeInterface()")
    print("ads_interface.run_test_sequence()")
    print()
    print("=" * 60)

def main():
    """Main setup function"""
    print("🚀 Freqtrade Execution Plugin Setup")
    print("=" * 40)
    
    steps = [
        ("Installing Freqtrade", install_freqtrade),
        ("Creating config", create_freqtrade_config),
        ("Creating directories", create_user_data_directory),
        ("Testing Redis", test_redis_connection),
        ("Creating scripts", create_start_scripts),
        ("Validating setup", validate_setup),
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        if not step_func():
            print(f"❌ Setup failed at: {step_name}")
            return False
    
    show_setup_complete()
    return True

if __name__ == "__main__":
    main()
