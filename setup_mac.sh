#!/bin/bash

# Product Description Generator - Mac Auto Setup Script
# This script automatically installs Python, dependencies, and Ollama for the Product Description Generator

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.11"
OLLAMA_VERSION="latest"
PROJECT_NAME="Product Description Generator"
APP_NAME="ProductDescriptionGenerator"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check macOS version
check_macos_version() {
    print_status "Checking macOS version..."
    
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This script is designed for macOS only"
        exit 1
    fi
    
    # Get macOS version
    MACOS_VERSION=$(sw_vers -productVersion)
    print_success "macOS version: $MACOS_VERSION"
    
    # Check if version is supported (10.13 or higher)
    if [[ $(echo "$MACOS_VERSION" | cut -d. -f1) -lt 10 ]] || 
       [[ $(echo "$MACOS_VERSION" | cut -d. -f1) -eq 10 && $(echo "$MACOS_VERSION" | cut -d. -f2) -lt 13 ]]; then
        print_warning "macOS 10.13 or higher is recommended for optimal performance"
    fi
}

# Function to install Homebrew
install_homebrew() {
    print_status "Checking for Homebrew..."
    
    if command_exists brew; then
        print_success "Homebrew is already installed"
        print_status "Updating Homebrew..."
        brew update
    else
        print_status "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for Apple Silicon Macs
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        
        print_success "Homebrew installed successfully"
    fi
}

# Function to install Python
install_python() {
    print_status "Checking for Python $PYTHON_VERSION..."
    
    # Check if Python is already installed with the right version
    if command_exists python3; then
        PYTHON_CURRENT_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d. -f1,2)
        if [[ "$PYTHON_CURRENT_VERSION" == "$PYTHON_VERSION" ]]; then
            print_success "Python $PYTHON_VERSION is already installed"
            return 0
        else
            print_warning "Python $PYTHON_CURRENT_VERSION found, but $PYTHON_VERSION is recommended"
        fi
    fi
    
    print_status "Installing Python $PYTHON_VERSION via Homebrew..."
    brew install python@$PYTHON_VERSION
    
    # Add Homebrew Python to PATH
    print_status "Adding Python to PATH..."
    
    # Add Homebrew Python bin directories to PATH
    if [[ $(uname -m) == "arm64" ]]; then
        # Apple Silicon Mac
        HOMEBREW_PYTHON_BIN="/opt/homebrew/opt/python@3.11/bin"
        HOMEBREW_PYTHON_FRAMEWORK_BIN="/opt/homebrew/opt/python@3.11/Frameworks/Python.framework/Versions/3.11/bin"
    else
        # Intel Mac
        HOMEBREW_PYTHON_BIN="/usr/local/opt/python@3.11/bin"
        HOMEBREW_PYTHON_FRAMEWORK_BIN="/usr/local/opt/python@3.11/Frameworks/Python.framework/Versions/3.11/bin"
    fi
    
    # Add Python directories to PATH
    echo "export PATH=\"$HOMEBREW_PYTHON_BIN:$HOMEBREW_PYTHON_FRAMEWORK_BIN:\$PATH\"" >> ~/.zprofile
    # echo "export PATH=\"$HOMEBREW_PYTHON_BIN:$HOMEBREW_PYTHON_FRAMEWORK_BIN:\$PATH\"" >> ~/.bash_profile
    export PATH="$HOMEBREW_PYTHON_BIN:$HOMEBREW_PYTHON_FRAMEWORK_BIN:$PATH"
    
    print_success "Python and pip added to PATH"
    
    print_success "Python $PYTHON_VERSION installed successfully"
}

# Function to install Python dependencies
install_python_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Check if requirements.txt exists
    if [[ ! -f "requirements.txt" ]]; then
        print_error "requirements.txt not found in current directory"
        print_status "Creating requirements.txt with known dependencies..."
        cat > requirements.txt << EOF
pandas==2.1.4
requests==2.31.0
ollama==0.1.7
customtkinter==5.2.0
python-dotenv==1.0.0
tqdm==4.66.1
retry==0.9.2
colorama==0.4.6
Pillow>=9.0.0
EOF
    fi
    
    # Determine the correct Python and pip commands
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
    
    # Check if we need to use versioned commands
    if command_exists python3.11; then
        PYTHON_CMD="python3.11"
        PIP_CMD="pip3.11"
        print_status "Using Python 3.11 specific commands"
    elif command_exists python3; then
        print_status "Using standard python3 command"
    else
        print_error "No Python 3 command found"
        return 1
    fi
    
    # Check if pip is available and install if needed
    if ! command_exists $PIP_CMD; then
        print_status "Installing pip using get-pip.py..."
        # Download and install pip using the official get-pip.py script
        curl -s https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD
        PIP_CMD="$PYTHON_CMD -m pip"
        print_status "Using python -m pip"
    else
        # Test if pip actually works
        if $PIP_CMD --version >/dev/null 2>&1; then
            print_success "Found working pip: $PIP_CMD"
        else
            print_warning "pip command found but not working, installing pip with get-pip.py..."
            curl -s https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD
            PIP_CMD="$PYTHON_CMD -m pip"
            print_status "Using python -m pip"
        fi
    fi
    
    # Test pip installation
    if $PIP_CMD --version >/dev/null 2>&1; then
        print_success "pip is working correctly"
        # Upgrade pip first
        print_status "Upgrading pip..."
        $PIP_CMD install --upgrade pip
    else
        print_error "pip installation failed. Please check your Python installation."
        return 1
    fi
    
    # Install tkinter support for Homebrew Python
    print_status "Installing tkinter support..."
    if [[ $(uname -m) == "arm64" ]]; then
        # Apple Silicon Mac
        brew install python-tk@3.11 2>/dev/null || print_warning "python-tk installation failed, trying alternative method"
    else
        # Intel Mac
        brew install python-tk@3.11 2>/dev/null || print_warning "python-tk installation failed, trying alternative method"
    fi
    
    # Install dependencies
    print_status "Installing dependencies from requirements.txt..."
    $PIP_CMD install -r requirements.txt
    
    print_success "Python dependencies installed successfully"
}

# Function to install Ollama
install_ollama() {
    print_status "Force reinstalling Ollama..."
    
    # Stop any running Ollama processes
    print_status "Stopping any running Ollama processes..."
    pkill -f ollama 2>/dev/null || true
    sleep 2
    
    # Remove existing Ollama installation
    if [[ -d "/Applications/Ollama.app" ]]; then
        print_status "Removing existing Ollama installation..."
        rm -rf "/Applications/Ollama.app"
    fi
    
    # Remove Ollama from PATH
    print_status "Cleaning up PATH configuration..."
    sed -i '' '/Ollama.app\/Contents\/Resources/d' ~/.zprofile 2>/dev/null || true
    # sed -i '' '/Ollama.app\/Contents\/Resources/d' ~/.bash_profile 2>/dev/null || true
    
    print_status "Installing Ollama..."
    
    # Download and install Ollama
    print_status "Downloading Ollama installer..."
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Download Ollama DMG
    OLLAMA_DMG_URL="https://ollama.ai/download/Ollama-darwin.zip"
    print_status "Downloading from: $OLLAMA_DMG_URL"
    
    if command_exists curl; then
        curl -L -o "Ollama-darwin.zip" "$OLLAMA_DMG_URL"
    elif command_exists wget; then
        wget -O "Ollama-darwin.zip" "$OLLAMA_DMG_URL"
    else
        print_error "Neither curl nor wget found. Please install one of them."
        exit 1
    fi
    
    # Extract and install
    print_status "Extracting Ollama installer..."
    unzip -q "Ollama-darwin.zip"
    
    # List contents to debug
    print_status "Checking extracted files..."
    ls -la
    
    # Move Ollama to Applications
    print_status "Installing Ollama to Applications..."
    if [[ -d "Ollama.app" ]]; then
        # Remove existing installation if it exists
        if [[ -d "/Applications/Ollama.app" ]]; then
            print_status "Removing existing Ollama installation..."
            rm -rf "/Applications/Ollama.app"
        fi
        cp -R "Ollama.app" "/Applications/"
        print_success "Ollama installed to Applications folder"
    elif [[ -f "Ollama.app" ]]; then
        # Remove existing installation if it exists
        if [[ -d "/Applications/Ollama.app" ]]; then
            print_status "Removing existing Ollama installation..."
            rm -rf "/Applications/Ollama.app"
        fi
        cp "Ollama.app" "/Applications/"
        print_success "Ollama installed to Applications folder"
    else
        print_error "Ollama.app not found in downloaded files"
        print_status "Available files:"
        ls -la
        exit 1
    fi
    
    # Clean up
    cd - > /dev/null
    rm -rf "$TEMP_DIR"
    
    # Add Ollama to PATH
    print_status "Adding Ollama to PATH..."
    echo 'export PATH="/Applications/Ollama.app/Contents/Resources:$PATH"' >> ~/.zprofile
    # echo 'export PATH="/Applications/Ollama.app/Contents/Resources:$PATH"' >> ~/.bash_profile
    
    # Source the profile to make it available in current session
    export PATH="/Applications/Ollama.app/Contents/Resources:$PATH"
    
    print_success "Ollama installed successfully"
}

# Function to start Ollama service
start_ollama() {
    print_status "Starting Ollama service..."
    
    # Check if Ollama is running
    if pgrep -f "ollama" > /dev/null; then
        print_success "Ollama is already running"
        return 0
    fi
    
    # Start Ollama
    print_status "Starting Ollama in background..."
    nohup /Applications/Ollama.app/Contents/Resources/ollama serve > /dev/null 2>&1 &
    
    # Wait a moment for it to start
    sleep 3
    
    # Check if it's running
    if pgrep -f "ollama" > /dev/null; then
        print_success "Ollama service started successfully"
    else
        print_warning "Ollama service may not have started properly"
        print_status "You may need to start it manually from Applications"
    fi
}

# Function to download and setup Ollama model
setup_ollama_model() {
    print_status "Force reinstalling Ollama model..."
    
    # Check if Ollama is available
    if ! command_exists ollama; then
        print_error "Ollama command not found. Please restart your terminal or run: source ~/.zprofile"
        return 1
    fi
    
    # Check if port 11434 is already in use
    if lsof -i :11434 > /dev/null 2>&1; then
        print_status "Port 11434 is already in use"
        print_status "Checking what's using the port..."
        lsof -i :11434
    fi
    
    # Start Ollama service if not running
    if ! pgrep -f "ollama" > /dev/null; then
        print_status "Starting Ollama service..."
        nohup ollama serve > /dev/null 2>&1 &
        sleep 3
    else
        print_status "Ollama process is already running"
    fi
    
    # Wait for Ollama to be ready
    print_status "Waiting for Ollama to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            print_success "Ollama service is ready"
            break
        fi
        if [[ $i -eq 30 ]]; then
            print_warning "Ollama service didn't start within 30 seconds"
            print_status "Trying to start Ollama manually..."
            
            # Try to start Ollama manually
            if [[ -d "/Applications/Ollama.app" ]]; then
                open "/Applications/Ollama.app"
                print_status "Opened Ollama.app - please wait for it to start..."
                sleep 5
                
                # Try one more time
                if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
                    print_success "Ollama service is now ready"
                    break
                else
                    print_error "Ollama service still not responding"
                    print_status "You may need to start Ollama manually from Applications"
                    return 1
                fi
            else
                print_error "Ollama.app not found in Applications"
                return 1
            fi
        fi
        sleep 1
    done
    
    # Check if model is already installed
    print_status "Checking for existing llama3.1:8b model..."
    if curl -s http://localhost:11434/api/tags | grep -q "llama3.1:8b"; then
        print_success "Model llama3.1:8b is already installed"
        return 0
    fi
    
    # Download the model
    print_status "Downloading llama3.1:8b model (this may take several minutes)..."
    print_warning "This is a large download (~4.9GB). Please be patient."
    
    if ollama pull llama3.1:8b; then
        print_success "Model downloaded successfully"
    else
        print_error "Failed to download model. Please check your internet connection and try again."
        return 1
    fi
}

# Function to create output directory with proper permissions
create_output_directory() {
    print_status "Creating output directory with proper permissions..."
    
    # Create output directory if it doesn't exist
    if [[ ! -d "output" ]]; then
        mkdir -p "output"
        print_success "Created output directory"
    else
        print_success "Output directory already exists"
    fi
    
    # Set proper permissions
    chmod 755 "output"
    print_success "Set output directory permissions"
    
    # Create a test file to verify write permissions
    if touch "output/test_write.tmp" 2>/dev/null; then
        rm -f "output/test_write.tmp"
        print_success "Write permissions verified"
    else
        print_warning "Write permissions test failed - you may need to run with sudo or check directory permissions"
    fi
}

# Function to create launcher script
create_launcher() {
    print_status "Creating launcher script..."
    
    cat > run_gui.sh << 'EOF'
#!/bin/bash

# Product Description Generator Launcher
# This script launches the GUI application

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Set up Python environment for Homebrew installations
if [[ $(uname -m) == "arm64" ]]; then
    # Apple Silicon Mac
    export PATH="/opt/homebrew/opt/python@3.11/bin:/opt/homebrew/opt/python@3.11/Frameworks/Python.framework/Versions/3.11/bin:$PATH"
else
    # Intel Mac
    export PATH="/usr/local/opt/python@3.11/bin:/usr/local/opt/python@3.11/Frameworks/Python.framework/Versions/3.11/bin:$PATH"
fi

# Determine the correct Python command
if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_CMD="python3.11"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please run the setup script first: ./setup_mac.sh"
    exit 1
fi

# Check if the GUI file exists
if [[ ! -f "gui.py" ]]; then
    echo "Error: gui.py not found in current directory"
    echo "Please make sure you're running this from the correct directory"
    exit 1
fi

# Test if tkinter is available (required for customtkinter)
if ! $PYTHON_CMD -c "import tkinter" 2>/dev/null; then
    echo "Error: tkinter is not available"
    echo "Installing tkinter support..."
    if command -v brew >/dev/null 2>&1; then
        if [[ $(uname -m) == "arm64" ]]; then
            brew install python-tk@3.11
        else
            brew install python-tk@3.11
        fi
    else
        echo "Homebrew not found. Please install tkinter manually or use system Python."
        exit 1
    fi
fi

# Test if customtkinter is available
if ! $PYTHON_CMD -c "import customtkinter" 2>/dev/null; then
    echo "Error: customtkinter is not available"
    echo "Trying to install customtkinter..."
    if $PYTHON_CMD -m pip install customtkinter; then
        echo "customtkinter installed successfully"
    else
        echo "Failed to install customtkinter. Please run the setup script again."
        exit 1
    fi
fi

# Launch the GUI
echo "Starting Product Description Generator..."
$PYTHON_CMD gui.py
EOF

    chmod +x run_gui.sh
    print_success "Launcher script created: run_gui.sh"
}

# Function to create desktop shortcut
create_desktop_shortcut() {
    print_status "Creating desktop shortcut..."
    
    # Create the app bundle directory structure
    mkdir -p "Product Description Generator.app/Contents/MacOS"
    
    # Create a simple AppleScript application
    cat > "Product Description Generator.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Product Description Generator</string>
    <key>CFBundleIdentifier</key>
    <string>com.productdescriptiongenerator.app</string>
    <key>CFBundleName</key>
    <string>Product Description Generator</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
</dict>
</plist>
EOF

    # Create the executable script
    mkdir -p "Product Description Generator.app/Contents/MacOS"
    cat > "Product Description Generator.app/Contents/MacOS/Product Description Generator" << EOF
#!/bin/bash
cd "$(dirname "$0")/../../.."
./run_gui.sh
EOF

    chmod +x "Product Description Generator.app/Contents/MacOS/Product Description Generator"
    
    print_success "Desktop shortcut created: Product Description Generator.app"
}

# Function to verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    local errors=0
    
    # Check Python
    if command_exists python3; then
        print_success "✓ Python 3 is installed"
    else
        print_error "✗ Python 3 is not installed"
        ((errors++))
    fi
    
    # Check Python packages
    PYTHON_CMD="python3"
    if command_exists python3.11; then
        PYTHON_CMD="python3.11"
    fi
    
    # Test each package individually for better error reporting
    local missing_packages=()
    
    # Test customtkinter (try different import methods)
    if $PYTHON_CMD -c "import customtkinter" 2>/dev/null; then
        print_success "✓ customtkinter is installed"
    elif $PYTHON_CMD -c "import customtkinter as ctk" 2>/dev/null; then
        print_success "✓ customtkinter is installed (as ctk)"
    elif $PYTHON_CMD -c "import tkinter; import customtkinter" 2>/dev/null; then
        print_success "✓ customtkinter is installed"
    else
        # Check if customtkinter is installed via pip
        if $PYTHON_CMD -m pip show customtkinter >/dev/null 2>&1; then
            print_success "✓ customtkinter is installed via pip"
        else
            # Try to install customtkinter
            print_status "Installing customtkinter..."
            if $PYTHON_CMD -m pip install customtkinter 2>/dev/null; then
                print_success "✓ customtkinter installed successfully"
            else
                missing_packages+=("customtkinter")
                print_error "✗ customtkinter installation failed"
            fi
        fi
    fi
    
    # Test other packages
    local packages=("pandas" "requests" "ollama")
    for package in "${packages[@]}"; do
        if $PYTHON_CMD -c "import $package" 2>/dev/null; then
            print_success "✓ $package is installed"
        else
            missing_packages+=("$package")
            print_error "✗ $package is missing"
        fi
    done
    
    if [[ ${#missing_packages[@]} -eq 0 ]]; then
        print_success "✓ All Python dependencies are installed"
    else
        print_error "✗ Missing Python packages: ${missing_packages[*]}"
        ((errors++))
    fi
    
    # Check Ollama
    if command_exists ollama; then
        print_success "✓ Ollama is installed"
    else
        print_error "✗ Ollama is not installed"
        ((errors++))
    fi
    
    # Check Ollama service
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "✓ Ollama service is running"
    else
        print_warning "⚠ Ollama service is not running (this is normal if you just installed it)"
    fi
    
    # Check GUI file
    if [[ -f "gui.py" ]]; then
        print_success "✓ GUI application file found"
    else
        print_error "✗ GUI application file (gui.py) not found"
        ((errors++))
    fi
    
    if [[ $errors -eq 0 ]]; then
        print_success "Installation verification completed successfully!"
        return 0
    else
        print_error "Installation verification found $errors error(s)"
        return 1
    fi
}

# Function to display final instructions
show_final_instructions() {
    echo
    echo "=========================================="
    echo "🎉 Setup Complete!"
    echo "=========================================="
    echo
    echo "Your Product Description Generator is now ready to use!"
    echo
    echo "📋 What was installed:"
    echo "   • Python $PYTHON_VERSION"
    echo "   • All required Python packages"
    echo "   • Ollama AI service"
    echo "   • Llama3.1:8b model"
    echo
    echo "🚀 How to run the application:"
    echo "   1. Double-click 'Product Description Generator.app' on your desktop"
    echo "   2. Or run: ./run_gui.sh"
    echo "   3. Or run: python3 gui.py"
    echo
    echo "🔧 First-time setup:"
    echo "   1. Launch the application"
    echo "   2. Click 'Setup Ollama' to verify the AI model is working"
    echo "   3. Test with a single product using the test section"
    echo
    echo "📁 Important files:"
    echo "   • gui.py - Main application"
    echo "   • run_gui.sh - Launcher script"
    echo "   • requirements.txt - Python dependencies"
    echo
    echo "🆘 Need help?"
    echo "   • Check the README.md file for detailed instructions"
    echo "   • Make sure Ollama is running: ollama serve"
    echo "   • Test Ollama: ollama list"
    echo
    echo "Enjoy using your Product Description Generator! 🎉"
    echo
}

# Main installation function
main() {
    echo "=========================================="
    echo "🚀 $PROJECT_NAME - Mac Auto Setup"
    echo "=========================================="
    echo
    echo "This script will automatically install:"
    echo "   • Python $PYTHON_VERSION"
    echo "   • All required dependencies"
    echo "   • Ollama AI service"
    echo "   • Llama3.1:8b model"
    echo
    echo "The installation may take 10-15 minutes depending on your internet speed."
    echo
    
    # Ask for confirmation
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    echo
    print_status "Starting installation process..."
    echo
    
    # Run installation steps
    check_macos_version
    install_homebrew
    install_python
    install_python_dependencies
    install_ollama
    start_ollama
    setup_ollama_model
    create_launcher
    create_desktop_shortcut
    
    echo
    print_status "Installation completed! Verifying..."
    echo
    
    # Verify installation
    if verify_installation; then
        show_final_instructions
    else
        print_error "Installation completed with some issues. Please check the errors above."
        echo
        echo "You can try running the application anyway:"
        echo "   ./run_gui.sh"
        echo
        echo "Or check the troubleshooting section in README.md"
    fi
}

# Run main function
main "$@"
