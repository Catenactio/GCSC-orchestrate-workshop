# IBM watsonx Orchestrate ADK Workshop

Build a **two-agent collaboration system** for film production logistics using the IBM watsonx Orchestrate Agent Development Kit (ADK).

## What You'll Learn

- Create custom Python tools with the `@tool` decorator
- Deploy agents via YAML/CLI
- Create agents in the Orchestrate UI
- **Use the collaborator feature** to enable agent-to-agent communication

## What You'll Build

A **Two-Agent System** where specialized AI agents collaborate:

```
┌────────────────────────────────────────────────────────────────┐
│                  TWO-AGENT COLLABORATION                        │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  PRODUCTION ASSISTANT (UI-Created)                       │   │
│  │  Focus: Slack + Procurement                              │   │
│  │                                                          │   │
│  │  Tools: post_briefing, send_approval_request, place_order│   │
│  │  Collaborator: → Data Coordinator                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           │ calls as collaborator               │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  DATA COORDINATOR (YAML/CLI)                             │   │
│  │  Focus: Notion + Airtable                                │   │
│  │                                                          │   │
│  │  Tools: get_schedule, search_inventory, check_availability│   │
│  │         create_reservation                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│         Notion              Airtable              Slack         │
│        (Schedule)          (Inventory)          (Comms)         │
└────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Python 3.10+
- API access to: Notion, Airtable, Slack, Google AI (see setup below)

---

## Setup Instructions

### Step 1: Create IBM Cloud Account & Start Orchestrate Trial

1. Go to [cloud.ibm.com](https://cloud.ibm.com) and create a free IBM Cloud account
2. Once logged in, search for **"watsonx Orchestrate"** in the catalog
3. Select the **Free Trial** plan and provision your instance
4. Wait for the instance to be ready (takes a few minutes)
5. Click **"Launch watsonx Orchestrate"** to open the UI

### Step 2: Install Orchestrate CLI & ADK

```bash
pip install ibm-watsonx-orchestrate
```

Verify installation:
```bash
orchestrate --version
```

### Step 3: Configure Orchestrate Environment

You need to connect the CLI to your Orchestrate instance.

**Get your API Key:**
1. In the Orchestrate UI, click **Settings** (gear icon)
2. Go to **API Keys**
3. Click **Create API Key**, give it a name, and copy the key

**Get your Instance URL:**
1. Look at your browser URL when in Orchestrate
2. Copy the base URL (e.g., `https://dl.watson-orchestrate.ibm.com/your-instance`)

**Add and activate the environment:**
```bash
# Add your environment
orchestrate env add -n <env-name> -u <your-instance-url>

# Activate it
orchestrate env activate <env-name>
# enter your wxo apikey when prompted 

# Verify connection
orchestrate agents list
```

### Step 4: Get External API Keys

<details>
<summary><strong>Airtable API Key & Base ID</strong></summary>

**Copy the workshop base:**
1. Go to [this Airtable template](https://airtable.com/appB2eRIBStCYXA6o/shrAQjTlfPdmHjU3h/tblyXLbRc0kniebrs/viw8jHelc0ixzi7y1)
2. Click **Copy base** to add it to your workspace

**Create an API token:**
1. Go to [airtable.com/create/tokens](https://airtable.com/create/tokens)
2. Click **Create new token**
3. Give it a name (e.g., "Orchestrate Workshop")
4. Add scopes:
   - `data.records:read`
   - `data.records:write`
5. Under **Access**, add your base
6. Click **Create token** and copy it

**Get your Base ID:**
- Open your Airtable base in the browser
- The URL looks like: `https://airtable.com/appXXXXXXXXXXXXXX/...`
- The Base ID is the part starting with `app` (e.g., `appXXXXXXXXXXXXXX`)

</details>

<details>
<summary><strong>Notion Integration Token & Database ID</strong></summary>

**Copy the workshop database:**
1. Go to [this Notion template](https://polished-chair-9ab.notion.site/2b312a00dbf58099aba5c4a169e4b7c3?v=2b312a00dbf5805aa324000c97b7b314)
2. Click **Duplicate** (top right) to add it to your workspace

**Create an integration:**
1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **New integration**
3. Name it (e.g., "Orchestrate Workshop")
4. Select the workspace
5. Click **Submit** and copy the **Internal Integration Secret**

**Share your database with the integration:**
1. Open your Notion database
2. Click **...** (menu) → **Add connections**
3. Select your integration

**Get your Database ID:**
- Open the database as a full page
- The URL looks like: `https://notion.so/Database-Name-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`
- The Database ID is the 32-character string (convert to UUID format with dashes)

</details>

<details>
<summary><strong>Slack Bot Token</strong></summary>

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App** → **From scratch**
3. Name it (e.g., "Production Assistant") and select your workspace
4. Go to **OAuth & Permissions**
5. Under **Bot Token Scopes**, add:
   - `chat:write`
   - `chat:write.public`
6. Click **Install to Workspace** and authorize
7. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

**Get your Channel ID:**
- In Slack, right-click a channel → **View channel details**
- Scroll to the bottom and copy the **Channel ID**

</details>

<details>
<summary><strong>Google Gemini API Key</strong></summary>

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **Create API Key**
3. Select or create a Google Cloud project
4. Copy the generated API key

</details>

### Step 5: Configure Credentials File

```bash
cp .env.example .env.credentials
```

Edit `.env.credentials` with your API keys:
```bash
# Airtable
AIRTABLE_API_KEY=pat...
AIRTABLE_INVENTORY_BASE_ID=app...

# Notion
NOTION_INTEGARTION_SECRET=secret_...
NOTION_DATABASE_UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C...

# Google Gemini
GOOGLE_API_KEY=...
```

---

## Quick Start

After completing setup above:

```bash

# Install Python dependencies
pip install -r requirements.txt

# Run the stand-alone tool tests to verify our credentials are working properly 
python tests/standalone_test.py

# Load credentials
source .env.credentials

# Deploy tools and Data Coordinator
./import-all.sh

# Create Production Assistant in UI
# See collaborator.md for step-by-step guide


```

---

## Project Structure

```
orchestrate/
├── skills/
│   ├── data.py              # 4 data tools (Notion + Airtable)
│   └── communications.py    # 3 communication tools (Slack)
│
├── agents/
│   └── data_coordinator.yaml # Data Coordinator agent
│
├── collaborator.md          # Guide for creating Production Assistant
├── import-all.sh            # Deploy everything
├── remove-all.sh            # Cleanup
└── *_connection.yaml        # Connection definitions
```

---

## Tools (7 Total)

### Data Tools - `skills/data.py`

| Tool | Connection | Purpose |
|------|------------|---------|
| `get_schedule` | Notion | Fetch upcoming scenes with script breakdown |
| `search_inventory` | Airtable | Fuzzy search assets by name |
| `check_availability` | Airtable | Check real-time availability for date |
| `create_reservation` | Notion + Airtable | Create allocation and update status |

### Communication Tools - `skills/communications.py`

| Tool | Connection | Purpose |
|------|------------|---------|
| `post_briefing` | Slack | Post formatted summary to channel |
| `send_approval_request` | Slack | Send interactive approval buttons |
| `place_order` | None | Execute mock procurement order |

---

## Agents (2)

### Data Coordinator (YAML/CLI)

- **File:** `agents/data_coordinator.yaml`
- **Focus:** Notion schedules and Airtable inventory
- **Deployed via:** `./import-all.sh`

### Production Assistant (UI)

- **Created in:** Orchestrate UI
- **Focus:** Slack communications and procurement
- **Has collaborator:** Data Coordinator
- **Setup guide:** [collaborator.md](collaborator.md)

---

## Demo Flow

```
1. User → Production Assistant: "Check the schedule for tomorrow"
   └─ Production Assistant calls Data Coordinator (collaborator)
   └─ Data Coordinator calls get_schedule
   └─ Returns schedule to Production Assistant
   └─ Production Assistant summarizes for user

2. User → Production Assistant: "Reserve 2 cameras for Scene 12"
   └─ Production Assistant calls Data Coordinator
   └─ Data Coordinator calls search_inventory + check_availability
   └─ Data Coordinator calls create_reservation
   └─ Returns confirmation
   └─ If >$100: Production Assistant calls send_approval_request

3. User → Production Assistant: "Post a briefing to Slack"
   └─ Production Assistant calls post_briefing (its own tool)
```

---

## Test Prompts

### Data Coordinator

```
"What scenes are scheduled for the next 2 days?"
"Search for Canon cameras"
"Is the Sony Venice available on December 10th?"
"Reserve 2 Canon 5D Mark IV for Scene 12 on December 8th"
```

### Production Assistant

```
"Check the schedule and tell me what equipment is needed"
"Post a briefing about tomorrow's shoot to Slack"
"Send an approval request for $150 camera rental"
"Reserve all equipment under $100 for Scene 12"
```

---

## Connections

| Connection | Type | Purpose |
|------------|------|---------|
| `gcsc_notion_api` | key_value | token + database_id |
| `gcsc_airtable_api` | key_value | token + base_id |
| `gcsc_slack_api` | bearer | bot token |
| `gcsc_google_ai` | key_value | api_key |

---

## Cleanup

```bash
./remove-all.sh
```

---

## Key Concepts

### Agent Collaboration

The Production Assistant has Data Coordinator as a **collaborator**. This means:
- Production Assistant can call Data Coordinator like a tool
- Data Coordinator handles all Notion/Airtable operations
- Production Assistant handles all Slack/procurement operations
- Clear separation of concerns

### Tool Development Pattern

```python
from ibm_watsonx_orchestrate.agent_builder.tools import tool
from ibm_watsonx_orchestrate.agent_builder.connections import ConnectionType

@tool(
    expected_credentials=[
        {"app_id": "gcsc_notion_api", "type": ConnectionType.KEY_VALUE}
    ],
    description="What this tool does"
)
def my_tool(input: MyInput) -> MyOutput:
    ...
```

---

**Built with IBM watsonx Orchestrate ADK**
