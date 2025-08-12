#!/usr/bin/env python3
"""
Product Description Generator
Automated generation of SEO-friendly titles and technical descriptions for industrial products.

Usage:
    python main.py process <input_file> [--output <output_file>]
    python main.py test <part_number> <manufacturer>
    python main.py setup
"""

import argparse
import sys
import logging
from pathlib import Path

from config import Config
from processor import ProductDescriptionProcessor

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('product_generator.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_ollama_installation():
    """Check if Ollama is installed and running"""
    import requests
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running and accessible")
            return True
        else:
            print("❌ Ollama is not responding properly")
            return False
    except requests.exceptions.RequestException:
        print("❌ Ollama is not running or not accessible")
        return False

def setup_ollama():
    """Setup Ollama with required model"""
    import subprocess
    import requests
    
    print("🔧 Setting up Ollama...")
    
    # Check if Ollama is installed
    try:
        subprocess.run(['ollama', '--version'], check=True, capture_output=True)
        print("✅ Ollama is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Ollama is not installed")
        print("Please install Ollama from: https://ollama.ai/")
        return False
    
    # Check if model is available using the new LLM client
    try:
        from llm_client import LLMClient
        config = Config()
        client = LLMClient(config)
        
        # Test connection
        if not client.test_connection():
            print("❌ Cannot connect to Ollama")
            return False
        
        # Check if model exists
        models = client.list_models()
        if 'llama3.1:8b' in models:
            print("✅ Llama3.1:8b model is already available")
            return True
        else:
            print("📥 Downloading Llama3.1:8b model...")
            if client.pull_model('llama3.1:8b'):
                print("✅ Model downloaded successfully")
                return True
            else:
                print("❌ Failed to download model")
                return False
                
    except Exception as e:
        print(f"❌ Error setting up Ollama: {str(e)}")
        return False

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="Product Description Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py process OPENAI.csv
  python main.py process OPENAI.csv --output results.csv
  python main.py test "XJG104HDG" "Eaton Crouse-Hinds"
  python main.py setup
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process a CSV file')
    process_parser.add_argument('input_file', help='Input CSV file path')
    process_parser.add_argument('--output', '-o', help='Output CSV file path (optional)')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test with a single product')
    test_parser.add_argument('part_number', help='Product part number')
    test_parser.add_argument('manufacturer', help='Product manufacturer')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup Ollama and required models')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    setup_logging()
    
    # Load configuration
    config = Config()
    
    try:
        if args.command == 'setup':
            print("🚀 Setting up Product Description Generator...")
            if setup_ollama():
                print("\n✅ Setup completed successfully!")
                print("You can now run: python main.py test 'PART_NUMBER' 'MANUFACTURER'")
            else:
                print("\n❌ Setup failed. Please check the errors above.")
                sys.exit(1)
        
        elif args.command == 'test':
            # Test with single product
            processor = ProductDescriptionProcessor(config)
            processor.process_single_product(args.part_number, args.manufacturer)
        
        elif args.command == 'process':
            # Check if input file exists
            if not Path(args.input_file).exists():
                print(f"❌ Input file not found: {args.input_file}")
                sys.exit(1)
            
            # Check Ollama setup
            if not check_ollama_installation():
                print("❌ Ollama is not properly set up")
                print("Run 'python main.py setup' to configure Ollama")
                sys.exit(1)
            
            # Process CSV file
            processor = ProductDescriptionProcessor(config)
            output_file = processor.process_csv(args.input_file, args.output)
            
            print(f"\n🎉 Processing completed!")
            print(f"Results saved to: {output_file}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logging.error(f"Application error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 