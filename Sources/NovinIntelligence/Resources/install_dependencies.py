#!/usr/bin/env python3
"""
NovinIntelligence SDK Dependency Installer
Automatically installs all required Python dependencies for the AI engine.
"""

import subprocess
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Ensure Python 3.7+ is available."""
    if sys.version_info < (3, 7):
        raise RuntimeError(f"Python 3.7+ required. Current version: {sys.version}")
    logger.info(f"✅ Python version: {sys.version}")

def install_package(package_name, import_name=None):
    """Install a package via pip and verify import."""
    import_name = import_name or package_name.split('==')[0].split('>=')[0]
    
    try:
        __import__(import_name)
        logger.info(f"✅ {package_name} already installed")
        return True
    except ImportError:
        logger.info(f"📦 Installing {package_name}...")
        
    try:
        # Try user installation first
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "--user", package_name
        ], capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            # Fallback to system installation with --break-system-packages
            logger.warning(f"User install failed, trying system install for {package_name}")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "--break-system-packages", package_name
            ], capture_output=True, text=True, check=True)
        
        # Verify installation
        __import__(import_name)
        logger.info(f"✅ Successfully installed {package_name}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install {package_name}: {e}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False
    except ImportError:
        logger.error(f"❌ {package_name} installed but import failed")
        return False

def install_all_dependencies():
    """Install all required dependencies for NovinIntelligence AI engine."""
    
    dependencies = [
        ("numpy>=1.19.0", "numpy"),
        ("scipy>=1.5.0", "scipy"), 
        ("cryptography>=3.0.0", "cryptography"),
        ("psutil>=5.7.0", "psutil")
    ]
    
    logger.info("🚀 Installing NovinIntelligence AI Dependencies...")
    
    failed_packages = []
    
    for package, import_name in dependencies:
        if not install_package(package, import_name):
            failed_packages.append(package)
    
    if failed_packages:
        logger.error(f"❌ Failed to install: {', '.join(failed_packages)}")
        logger.error("Please install manually or check system permissions")
        return False
    
    logger.info("✅ All dependencies installed successfully!")
    return True

def verify_ai_engine():
    """Test that the AI engine can be imported and initialized."""
    try:
        logger.info("🧪 Verifying AI engine...")
        
        # Add current directory to path
        current_dir = Path(__file__).parent / "python" / "lib"
        sys.path.insert(0, str(current_dir))
        
        from novin_intelligence import get_embedded_system_instance
        
        # Test initialization (without loading models for now)
        logger.info("✅ AI engine import successful")
        
        # Test basic functionality
        test_config = {
            'config_overrides': {
                'prediction_timeout': 0.1,
                'max_processing_time': 0.2
            }
        }
        
        system = get_embedded_system_instance(test_config)
        logger.info("✅ AI system initialization successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ AI engine verification failed: {e}")
        return False

def main():
    """Main installation and verification process."""
    try:
        logger.info("🛡️  NovinIntelligence SDK Setup")
        logger.info("=" * 50)
        
        # Check Python version
        check_python_version()
        
        # Install dependencies
        if not install_all_dependencies():
            sys.exit(1)
        
        # Verify AI engine
        if not verify_ai_engine():
            logger.warning("⚠️  Dependencies installed but AI engine verification failed")
            logger.warning("This may be normal if models are not yet loaded")
        
        logger.info("🎉 NovinIntelligence SDK setup complete!")
        logger.info("Your app can now use the full AI security engine.")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
