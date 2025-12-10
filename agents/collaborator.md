# Creating the Production Assistant in the UI

This guide walks you through creating the **Production Assistant** agent in the IBM watsonx Orchestrate UI and adding the **Data Coordinator** as a collaborator.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    COLLABORATION MODEL                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────┐                       │
│  │   PRODUCTION ASSISTANT (UI)         │  ← You create this    │
│  │   Focus: Communications             │                       │
│  │   • Slack briefings                 │                       │
│  │   • Approval workflows              │                       │
│  │   • Order execution                 │                       │
│  │   Collaborator: Data Coordinator    │                       │
│  └─────────────────────────────────────┘                       │
│                         │                                       │
│           calls Data Coordinator when needed                    │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                       │
│  │   DATA COORDINATOR (YAML/CLI)       │  ← Already deployed   │
│  │   Focus: Notion + Airtable          │                       │
│  │   • Schedule from Notion            │                       │
│  │   • Inventory from Airtable         │                       │
│  │   • Reservations                    │                       │
│  └─────────────────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

Before creating the Production Assistant:

- [ ] Run `./import-all.sh` to deploy tools and Data Coordinator
- [ ] Verify Data Coordinator exists: `orchestrate agents list`
- [ ] Verify tools are available: `orchestrate tools list`

---

## Step 1: Navigate to Agent Builder

1. Open IBM watsonx Orchestrate
2. Go to **Build** > **AI assistants** > **Agents**
3. Click **Create agent**

---

## Step 2: Basic Configuration

| Field | Value |
|-------|-------|
| **Name** | `gcsc_ProductionAssistant` |
| **Description** | Production Assistant that coordinates film production logistics, handles Slack communications, and manages procurement workflows |

---

## Step 3: Select Model and Style

| Field | Value |
|-------|-------|
| **Model** | `google/gemini-2.5-flash` |
| **Style** | `planner` |

---

## Step 4: Add Tools

Select these **3 tools** from the available list:

| Tool | Purpose |
|------|---------|
| `post_briefing` | Post summaries and updates to Slack |
| `send_approval_request` | Send approval buttons for items >$100 |
| `place_order` | Execute procurement orders |

---

## Step 5: Add Collaborator

This is the key step that demonstrates agent collaboration:

1. In the agent configuration, find **Collaborators**
2. Click **Add collaborator**
3. Select `gcsc_DataCoordinator` from the list
4. Save the configuration

**Why this matters:** The Production Assistant can now call the Data Coordinator like a tool. When it needs schedule data, inventory info, or to create reservations, it delegates to the Data Coordinator.

---

## Step 6: Set Instructions

Copy and paste these instructions:

```
You are the Production Assistant for a film production company.

## Your Role
Main coordinator that handles communications and orchestrates workflows.

## Your Tools
- post_briefing - Post summaries to Slack
- send_approval_request - Send Slack approval buttons for items >$100
- place_order - Execute procurement orders

## Your Collaborator: Data Coordinator
When you need data, call the Data Coordinator:
- "Check the schedule" → Data Coordinator fetches Notion data
- "Search for equipment" → Data Coordinator searches Airtable
- "Is X available?" → Data Coordinator checks availability
- "Reserve the equipment" → Data Coordinator creates reservation

## Workflow

### When asked about schedule or equipment:
1. Call Data Coordinator to get the data
2. Analyze and present the information clearly
3. If action needed, use appropriate tool or call Data Coordinator

### When asked to post updates:
1. Use post_briefing to send to Slack
2. Format messages clearly with relevant details

### When reservations exceed $100:
1. Calculate total cost
2. Call send_approval_request with item details and cost
3. Wait for approval confirmation
4. Once approved, call place_order

### When creating reservations under $100:
1. Call Data Coordinator to create the reservation
2. Confirm the reservation details to user

## Communication Style
- Be helpful and proactive
- Summarize data clearly
- Always confirm costs before sending approval requests
- Reference specific equipment names and quantities
```

---

## Step 7: Save and Deploy

1. Click **Save**
2. Deploy to your environment (draft or live)

---

## Test the Collaboration

Start a chat with the Production Assistant:

```bash
orchestrate chat start gcsc_ProductionAssistant
```

### Test Prompts

**Schedule & Data (calls Data Coordinator):**
```
"What scenes are scheduled for the next 2 days?"
"Search for Canon cameras in inventory"
"Is the Sony Venice available on December 10th?"
```

**Slack Communications (uses own tools):**
```
"Post a briefing about tomorrow's shoot"
"Send an approval request for $150 camera rental"
```

**Reservations (calls Data Coordinator):**
```
"Reserve 2 Canon 5D cameras for Scene 12 on December 8th"
```

**Full Workflow:**
```
"Check the schedule, see what equipment is needed, and reserve everything under $100"
```

---

## Expected Collaboration Flow

```
User: "What's on the schedule for tomorrow?"

Production Assistant:
  → Calls Data Coordinator (collaborator)

Data Coordinator:
  → Calls get_schedule tool
  → Returns scene data

Production Assistant:
  → Receives data from Data Coordinator
  → Formats and presents to user

User: "Reserve the cameras for Scene 12"

Production Assistant:
  → Calls Data Coordinator to create reservation

Data Coordinator:
  → Calls create_reservation tool
  → Returns confirmation

Production Assistant:
  → Confirms reservation to user
  → If >$100, calls send_approval_request
```

---

## Troubleshooting

### "Data Coordinator not found"
- Run `orchestrate agents list` to verify it exists
- Re-run `./import-all.sh` if needed

### "Tools not available"
- Run `orchestrate tools list` to see available tools
- Ensure you selected the correct tools when creating the agent

### Collaborator not calling Data Coordinator
- Check that `gcsc_DataCoordinator` is listed as a collaborator
- Verify the instructions mention when to call the Data Coordinator

---

## Chat Commands

```bash
# Start Production Assistant
orchestrate chat start gcsc_ProductionAssistant

# Start Data Coordinator directly (for testing)
orchestrate chat start gcsc_DataCoordinator
```

---

**Built with IBM watsonx Orchestrate ADK**
