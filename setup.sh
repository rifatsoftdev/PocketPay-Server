#!/bin/bash

set -e

echo "=========================================="
echo "  PocketPay Server Setup Script"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file already exists${NC}"
    read -p "Do you want to recreate it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing .env file"
    else
        rm .env
    fi
else
    echo -e "${GREEN}✓ Creating .env file...${NC}"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=sqlite:///./pocketpay.db
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# Email Configuration (SMTP)
EMAIL_ADDRESS=your-email@example.com
EMAIL_PASSWORD=your-email-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id

# JWT Authentication
SECRET_KEY=change-this-secret-key
ALGORITHM=HS256
ACCESS_EXPIRE=30
REFRESH_EXPIRE=10080

# OTP and Password Reset
OTP_TOKEN_EXPIRE_MIN=5
PASS_RST_TOKEN_EXPIRE_MIN=15

# User Rewards Configuration
NEW_USER_REWARD_WITH_REFERRAL=0
NEW_USER_REWARD_WITH_NO_REFERRAL=0
USER_REFERRAL_REWARD=0
SERVICE_CHARGE=0

# Application Settings
VERSION=1.0.0
DEBUG=True

# Cloudinary (Image Upload)
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret

# Security
SALT=change-this-salt
SERVICE_ACCOUNT_PATH=path/to/firebase-service-account.json

# Default Admin Credentials
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PHONE=+8801000000000
DEFAULT_ADMIN_PASSWORD=admin-password
DEFAULT_ADMIN_NAME=Admin

# Default Test User Credentials
DEFAULT_USER_EMAIL=user@example.com
DEFAULT_USER_PHONE=+8801000000001
DEFAULT_USER_PASSWORD=user-password
DEFAULT_USER_NAME=User
EOF
    echo -e "${GREEN}✓ .env file created successfully!${NC}"
fi

echo ""
echo "=========================================="
echo "  Setup Options"
echo "=========================================="
echo ""
echo "1. Setup with Docker (Recommended)"
echo "2. Setup without Docker (Manual)"
echo ""
read -p "Choose an option (1 or 2): " -n 1 -r
echo
echo ""

if [[ $REPLY =~ ^[1]$ ]]; then
    echo -e "${GREEN}Setting up with Docker...${NC}"
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi
    
    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}✗ Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}📝 Please update the .env file with your credentials before proceeding.${NC}"
    echo ""
    read -p "Have you updated the .env file? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please update .env file and run this script again."
        exit 0
    fi
    
    echo ""
    echo -e "${GREEN}Building Docker image...${NC}"
    docker-compose build
    
    echo ""
    echo -e "${GREEN}Starting PocketPay Server...${NC}"
    docker-compose up -d
    
    echo ""
    echo -e "${GREEN}✓ Setup complete!${NC}"
    echo ""
    echo "=========================================="
    echo "  Docker Setup Complete"
    echo "=========================================="
    echo ""
    echo -e "🚀 PocketPay Server is running at:"
    echo -e "   ${GREEN}http://localhost:8000${NC}"
    echo ""
    echo -e "📚 API Documentation:"
    echo -e "   ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "🔐 Admin Login:"
    echo -e "   ${GREEN}http://localhost:8000/admin/login${NC}"
    echo ""
    echo "View logs:"
    echo -e "   ${GREEN}docker-compose logs -f${NC}"
    echo ""
    echo "Stop server:"
    echo -e "   ${GREEN}docker-compose down${NC}"
    echo ""
    
elif [[ $REPLY =~ ^[2]$ ]]; then
    echo -e "${GREEN}Setting up without Docker...${NC}"
    
    # Check if Python 3.10+ is installed
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python 3 is not installed. Please install Python 3.10 or newer.${NC}"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo "Python version: $PYTHON_VERSION"
    
    echo ""
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
    
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source venv/bin/activate
    
    echo -e "${GREEN}Upgrading pip...${NC}"
    pip install --upgrade pip
    
    echo -e "${GREEN}Installing dependencies...${NC}"
    pip install -r requirements.txt
    
    echo ""
    echo -e "${YELLOW}📝 Please update the .env file with your credentials before proceeding.${NC}"
    echo ""
    read -p "Have you updated the .env file? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please update .env file and run this script again."
        exit 0
    fi
    
    echo ""
    echo -e "${GREEN}✓ Setup complete!${NC}"
    echo ""
    echo "=========================================="
    echo "  Manual Setup Complete"
    echo "=========================================="
    echo ""
    echo "To start the server, run:"
    echo -e "   ${GREEN}source venv/bin/activate${NC}"
    echo -e "   ${GREEN}python run.py${NC}"
    echo ""
    echo "Or use Uvicorn directly:"
    echo -e "   ${GREEN}uvicorn app.main:app --reload --host 0.0.0.0 --port 8000${NC}"
    echo ""
    
else
    echo -e "${RED}Invalid option. Please choose 1 or 2.${NC}"
    exit 1
fi

echo ""
