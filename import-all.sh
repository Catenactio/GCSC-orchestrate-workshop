#!/bin/bash

# IBM watsonx Orchestrate - Build and Import Script
# Imports tools and Data Coordinator agent for the two-agent workshop

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "================================================"
echo "  Production Logistics Workshop - Deploy"
echo "================================================"
echo ""

# Check if orchestrate CLI is available
if ! command -v orchestrate &> /dev/null; then
    echo -e "${RED}✗ orchestrate CLI not found${NC}"
    echo "  Please install: pip install ibm-watsonx-orchestrate"
    exit 1
fi

# Check environment variables
echo -e "${BLUE}▸ Validating environment configuration...${NC}"
python main.py

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Environment validation failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment validated${NC}"
echo ""

# Check orchestrate environment is active
echo -e "${BLUE}▸ Checking Orchestrate environment...${NC}"
if ! orchestrate env list 2>&1 | grep -q "^\*"; then
    echo -e "${RED}✗ No Orchestrate environment is active${NC}"
    echo "  Please activate an environment first:"
    echo "    orchestrate env add <name> --api-key <key> --url <url>"
    echo "    orchestrate env activate <name>"
    exit 1
fi
ACTIVE_ENV=$(orchestrate env list 2>&1 | grep "^\*" | awk '{print $2}')
echo -e "${GREEN}✓ Environment active: ${ACTIVE_ENV}${NC}"
echo ""

# Import connections
echo -e "${BLUE}▸ Importing connection configurations...${NC}"
orchestrate connections import -f connections/notion_connection.yaml > /dev/null 2>&1 || true
orchestrate connections import -f connections/airtable_connection.yaml > /dev/null 2>&1 || true
orchestrate connections import -f connections/slack_connection.yaml > /dev/null 2>&1 || true

# Create Google AI connection
orchestrate connections add -a gcsc_google_ai > /dev/null 2>&1 || true
orchestrate connections configure -a gcsc_google_ai --env draft -k key_value -t team > /dev/null 2>&1 || true

echo -e "${GREEN}✓ Connections configured${NC}"
echo ""

# Set connection credentials
echo -e "${BLUE}▸ Setting connection credentials...${NC}"

# Load environment variables
if [ -f .env.credentials ]; then
    source .env.credentials
else
    echo -e "${RED}✗ .env.credentials file not found${NC}"
    exit 1
fi

# Set credentials
orchestrate connections set-credentials --app-id gcsc_slack_api --env draft \
  -e "token=$SLACK_BOT_TOKEN" \
  -e "channel_id=$SLACK_CHANNEL_ID" > /dev/null 2>&1

orchestrate connections set-credentials --app-id gcsc_notion_api --env draft \
  -e "token=$NOTION_INTEGARTION_SECRET" \
  -e "database_id=$NOTION_DATABASE_UUID" > /dev/null 2>&1

orchestrate connections set-credentials --app-id gcsc_airtable_api --env draft \
  -e "token=$AIRTABLE_API_KEY" \
  -e "base_id=$AIRTABLE_INVENTORY_BASE_ID" > /dev/null 2>&1

orchestrate connections set-credentials --app-id gcsc_google_ai --env draft \
  -e "api_key=$GOOGLE_API_KEY" > /dev/null 2>&1

echo -e "${GREEN}✓ Credentials configured${NC}"
echo ""

# Import tools to Orchestrate
echo -e "${BLUE}▸ Importing tools...${NC}"

echo "  → Data tools (Notion + Airtable)..."
orchestrate tools import -k python \
  -f skills/data.py \
  -r requirements.txt \
  -a gcsc_notion_api \
  -a gcsc_airtable_api

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Data tools import failed${NC}"
    exit 1
fi

echo "  → Communication tools (Slack)..."
orchestrate tools import -k python \
  -f skills/communications.py \
  -r requirements.txt \
  -a gcsc_slack_api

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Communication tools import failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Tools imported${NC}"
echo ""

# Import Google AI model
echo -e "${BLUE}▸ Importing AI model...${NC}"
orchestrate models import --file google_model.yaml --app-id gcsc_google_ai

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Model import failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Model imported${NC}"
echo ""

# Import agent configuration
echo -e "${BLUE}▸ Importing Data Coordinator agent...${NC}"
orchestrate agents import --file agents/data_coordinator.yaml

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Agent import failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Agent imported${NC}"
echo ""

# Summary
echo "================================================"
echo -e "${GREEN}✓ Deployment complete!${NC}"
echo "================================================"
echo ""
echo -e "${BLUE}Deployed Resources:${NC}"
echo ""
echo "  Connections (4):"
echo "    • gcsc_notion_api (Notion database)"
echo "    • gcsc_airtable_api (Inventory base)"
echo "    • gcsc_slack_api (Team channel)"
echo "    • gcsc_google_ai (Gemini model)"
echo ""
echo "  Tools (7):"
echo "    Data:"
echo "      • get_schedule"
echo "      • search_inventory"
echo "      • check_availability"
echo "      • create_reservation"
echo "    Communications:"
echo "      • post_briefing"
echo "      • send_approval_request"
echo "      • place_order"
echo ""
echo "  Agents (1):"
echo "    • gcsc_DataCoordinator (YAML/CLI)"
echo ""
echo "================================================"
echo -e "${BLUE}Next Steps:${NC}"
echo "================================================"
echo ""
echo "  1. Test Data Coordinator:"
echo "     orchestrate chat start gcsc_DataCoordinator"
echo ""
echo "  2. Create Production Assistant in UI:"
echo "     • Open Orchestrate UI"
echo "     • Create new agent: gcsc_ProductionAssistant"
echo "     • Add tools: post_briefing, send_approval_request, place_order"
echo "     • Add collaborator: gcsc_DataCoordinator"
echo "     • See collaborator.md for detailed instructions"
echo ""
echo "  3. Test the collaboration:"
echo "     orchestrate chat start gcsc_ProductionAssistant"
echo ""
