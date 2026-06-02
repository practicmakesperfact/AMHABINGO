#!/bin/bash

# AMHABINGO Deployment Script
# This script helps deploy both frontend and backend

set -e  # Exit on error

echo "🎮 AMHABINGO Deployment Script"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if required commands exist
check_dependencies() {
    echo "Checking dependencies..."
    
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    print_success "All dependencies are installed"
}

# Deploy Frontend
deploy_frontend() {
    echo ""
    echo "📦 Deploying Frontend..."
    echo "========================"
    
    cd frontend
    
    # Install dependencies
    echo "Installing frontend dependencies..."
    npm install
    
    # Build
    echo "Building frontend..."
    npm run build
    
    # Check if Vercel CLI is installed
    if command -v vercel &> /dev/null; then
        echo ""
        echo "Deploy to Vercel? (y/n)"
        read -r deploy_vercel
        
        if [ "$deploy_vercel" = "y" ]; then
            vercel --prod
            print_success "Frontend deployed to Vercel!"
        else
            print_warning "Skipping Vercel deployment"
        fi
    else
        print_warning "Vercel CLI not installed. Install with: npm install -g vercel"
    fi
    
    cd ..
}

# Deploy Backend
deploy_backend() {
    echo ""
    echo "🚀 Deploying Backend..."
    echo "======================="
    
    cd backend
    
    # Create virtual environment if not exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
    
    # Initialize database if not exists
    if [ ! -f "bingo.db" ]; then
        echo "Initializing database..."
        python init_db.py
        python init_cartelas.py
        print_success "Database initialized with 600 cartelas"
    else
        print_warning "Database already exists. Skipping initialization."
    fi
    
    # Check if Railway CLI is installed
    if command -v railway &> /dev/null; then
        echo ""
        echo "Deploy to Railway? (y/n)"
        read -r deploy_railway
        
        if [ "$deploy_railway" = "y" ]; then
            railway up
            print_success "Backend deployed to Railway!"
        else
            print_warning "Skipping Railway deployment"
        fi
    else
        print_warning "Railway CLI not installed. Install with: npm install -g @railway/cli"
    fi
    
    deactivate
    cd ..
}

# Test locally
test_local() {
    echo ""
    echo "🧪 Testing Locally..."
    echo "===================="
    
    # Start backend in background
    echo "Starting backend..."
    cd backend
    source venv/bin/activate
    python -m uvicorn app.main:app --reload &
    BACKEND_PID=$!
    deactivate
    cd ..
    
    # Start frontend in background
    echo "Starting frontend..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    echo ""
    print_success "Services started!"
    echo "Frontend: http://localhost:3000"
    echo "Backend: http://localhost:8000"
    echo ""
    echo "Press Ctrl+C to stop"
    
    # Wait for user interrupt
    trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
    wait
}

# Main menu
show_menu() {
    echo ""
    echo "What would you like to do?"
    echo "1) Deploy Frontend only"
    echo "2) Deploy Backend only"
    echo "3) Deploy Both"
    echo "4) Test Locally"
    echo "5) Exit"
    echo ""
    read -p "Enter choice [1-5]: " choice
    
    case $choice in
        1)
            check_dependencies
            deploy_frontend
            ;;
        2)
            check_dependencies
            deploy_backend
            ;;
        3)
            check_dependencies
            deploy_backend
            deploy_frontend
            ;;
        4)
            check_dependencies
            test_local
            ;;
        5)
            echo "Goodbye! 👋"
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            show_menu
            ;;
    esac
}

# Start
check_dependencies
show_menu

print_success "Deployment complete! 🎉"
