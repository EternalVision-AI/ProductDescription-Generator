#!/usr/bin/env python3
"""
Test script to validate the Product Description Generator installation
"""

import sys
import importlib
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    required_modules = [
        'pandas',
        'requests', 
        'ollama',
        'customtkinter',
        'python-dotenv',
        'tqdm',
        'retry',
        'colorama'
    ]
    
    print("Testing module imports...")
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module.replace('-', '_'))
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        print("Please run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All modules imported successfully!")
        return True

def test_local_modules():
    """Test if local application modules can be imported"""
    local_modules = [
        'config',
        'llm_client', 
        'processor'
    ]
    
    print("\nTesting local module imports...")
    failed_imports = []
    
    for module in local_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import local modules: {', '.join(failed_imports)}")
        return False
    else:
        print("✅ All local modules imported successfully!")
        return True

def test_ollama_connection():
    """Test Ollama connection"""
    print("\nTesting Ollama connection...")
    
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running and accessible")
            return True
        else:
            print("❌ Ollama is not responding properly")
            return False
    except requests.exceptions.RequestException:
        print("❌ Ollama is not running or not accessible")
        print("Please install and start Ollama: https://ollama.ai/")
        return False

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config import Config
        config = Config()
        print(f"✅ Configuration loaded")
        print(f"   Ollama Model: {config.OLLAMA_MODEL}")
        print(f"   Batch Size: {config.BATCH_SIZE}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_llm_client():
    """Test LLM client setup"""
    print("\nTesting LLM client...")
    
    try:
        from config import Config
        from llm_client import LLMClient
        
        config = Config()
        client = LLMClient(config)
        print("✅ LLM client created successfully")
        return True
    except Exception as e:
        print(f"❌ LLM client error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Product Description Generator - Installation Test")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Local Modules", test_local_modules),
        ("Configuration", test_config),
        ("LLM Client", test_llm_client),
        ("Ollama Connection", test_ollama_connection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Installation is complete.")
        print("\nNext steps:")
        print("1. Run: python main.py setup")
        print("2. Test with: python main.py test 'XJG104HDG' 'Eaton Crouse-Hinds'")
        print("3. Or launch GUI: python gui.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nCommon solutions:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Install Ollama: https://ollama.ai/")
        print("3. Start Ollama: ollama serve")
    
    print("=" * 50)

if __name__ == '__main__':
    main() 