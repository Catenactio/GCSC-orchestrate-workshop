#!/bin/bash

# IBM watsonx Orchestrate - Remove All GCSC Resources
# Removes all gcsc_ prefixed resources from the active Orchestrate environment

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "================================================"
echo "  GCSC Resources Cleanup"
echo "================================================"
echo ""
echo -e "${YELLOW}This will remove all gcsc_ prefixed resources.${NC}"
echo ""

# Confirmation prompt
read -p "Are you sure you want to proceed? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Aborted.${NC}"
    exit 0
fi

echo ""

# Track what was removed
AGENTS_REMOVED=0
TOOLS_REMOVED=0
CONNECTIONS_REMOVED=0

# Remove agents
echo -e "${BLUE}▸ Removing agents...${NC}"

if orchestrate agents remove --name gcsc_DataCoordinator --kind native > /dev/null 2>&1; then
    echo "  ✓ gcsc_DataCoordinator"
    ((AGENTS_REMOVED++))
fi

if orchestrate agents remove --name gcsc_ProductionAssistant --kind native > /dev/null 2>&1; then
    echo "  ✓ gcsc_ProductionAssistant"
    ((AGENTS_REMOVED++))
fi

if [ $AGENTS_REMOVED -eq 0 ]; then
    echo -e "  ${YELLOW}No agents found${NC}"
else
    echo -e "${GREEN}✓ Removed $AGENTS_REMOVED agent(s)${NC}"
fi
echo ""

# Remove tools
echo -e "${BLUE}▸ Removing tools...${NC}"

# Data tools
TOOLS=("get_schedule" "search_inventory" "check_availability" "create_reservation")
for tool in "${TOOLS[@]}"; do
    if orchestrate tools remove -n "$tool" > /dev/null 2>&1; then
        echo "  ✓ $tool"
        ((TOOLS_REMOVED++))
    fi
done

# Communication tools
TOOLS=("post_briefing" "send_approval_request" "place_order")
for tool in "${TOOLS[@]}"; do
    if orchestrate tools remove -n "$tool" > /dev/null 2>&1; then
        echo "  ✓ $tool"
        ((TOOLS_REMOVED++))
    fi
done


if [ $TOOLS_REMOVED -eq 0 ]; then
    echo -e "  ${YELLOW}No tools found${NC}"
else
    echo -e "${GREEN}✓ Removed $TOOLS_REMOVED tool(s)${NC}"
fi
echo ""

# Remove connections
echo -e "${BLUE}▸ Removing connections...${NC}"

CONNECTIONS=("gcsc_notion_api" "gcsc_airtable_api" "gcsc_slack_api" "gcsc_google_ai")
for conn in "${CONNECTIONS[@]}"; do
    if orchestrate connections remove --app-id "$conn" > /dev/null 2>&1; then
        echo "  ✓ $conn"
        ((CONNECTIONS_REMOVED++))
    fi
done

if [ $CONNECTIONS_REMOVED -eq 0 ]; then
    echo -e "  ${YELLOW}No connections found${NC}"
else
    echo -e "${GREEN}✓ Removed $CONNECTIONS_REMOVED connection(s)${NC}"
fi
echo ""

# Summary
echo "================================================"
echo -e "${GREEN}✓ Cleanup complete!${NC}"
echo "================================================"
echo ""
echo "Removed:"
echo "  • Agents: $AGENTS_REMOVED"
echo "  • Tools: $TOOLS_REMOVED"
echo "  • Connections: $CONNECTIONS_REMOVED"
echo ""

# Show remaining resources
echo "================================================"
echo -e "${BLUE}Remaining resources:${NC}"
echo "================================================"
echo ""

echo "Agents:"
if orchestrate agents list 2>/dev/null | grep -q "No agents found"; then
    echo "  (none)"
else
    orchestrate agents list 2>/dev/null | sed 's/^/  /'
fi
echo ""

echo "Tools:"
TOOL_COUNT=$(orchestrate tools list 2>/dev/null | grep -c "^" || echo "0")
if [ "$TOOL_COUNT" -eq 0 ]; then
    echo "  (none)"
else
    echo "  $TOOL_COUNT tools remain"
fi
echo ""

echo "Connections:"
CONN_COUNT=$(orchestrate connections list 2>/dev/null | grep -c "^" || echo "0")
if [ "$CONN_COUNT" -eq 0 ]; then
    echo "  (none)"
else
    echo "  $CONN_COUNT connections remain"
fi
echo ""
