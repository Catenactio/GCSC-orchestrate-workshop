# Project: Production Logistics Workshop

**Platform:** IBM watsonx Orchestrate (SaaS)
**Tools:** Orchestrate ADK (Python SDK) & CLI
**Workshop Guide:** See [README.md](README.md) for setup instructions

## Overview

This workshop builds a two-agent collaboration system for film production logistics:

- **Data Coordinator** (YAML/CLI) - Handles Notion schedules and Airtable inventory
- **Production Assistant** (UI-created) - Handles Slack communications, has Data Coordinator as collaborator

## Key Concepts

1. **Agent Collaboration** - Production Assistant calls Data Coordinator like a tool
2. **System-Based Split** - Data operations vs Communication operations
3. **UI Agent Creation** - Demonstrates creating agents in Orchestrate UI

## Data Models & Schema

### Notion Database: "Shooting Schedule"

**Table Structure:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `Scene Number` | Title (Rich Text) | Primary identifier | "Scene 15" |
| `Shoot Date` | Date | Scheduled filming date | "2025-12-08" |
| `Est. Budget` | Number (Currency) | Estimated cost for scene equipment | null (calculated) |
| `Logistics Status` | Select | Status: Draft, Pending, Reserved, Complete | "Draft" |
| `Scene Description` | Text | Location and scene context | "Car Chase B-Roll<br>Ext. Coastal Highway" |
| `Script Breakdown` | Rich Text | Unstructured equipment needs | "Driving shots. We need the DJI Mavic drone for aerials and 4 GoPro HERO10s..." |

**Example Record:**
```json
{
  "scene_id": "2b312a00-dbf5-8044-836c-c94d690d069f",
  "scene_number": "Scene 15",
  "shoot_date": "2025-12-08",
  "script_breakdown": "Driving shots. We need the DJI Mavic drone for aerials and 4 GoPro HERO10s to mount on the bumper.",
  "est_budget": null,
  "logistics_status": "Draft"
}
```

**Demo Data (5 scenes, Dec 8-12, 2025):**
- Scene 15: Car Chase B-Roll - needs DJI Mavic drone, 4 GoPro HERO10s
- Scene 22: Dailies Review - needs MacBook Pro, 20 GoPros
- Scene 25: Hero Product Shot - needs Sony PXW-FS7 (high frame rate)
- Scene 18: Podcast Roundtable - needs Yamaha Mixer, 15 Shure SM7B Microphones
- Scene 12: CEO Interview - needs 2 Canon 5D Mark IVs, Canon 24-70mm lens, 2 Sennheiser lavs, Dell Monitor

---

### Airtable Base: "Film Production Inventory"

#### Table 1: "Assets"

**Table Structure:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `Asset Name` | Single Line Text (Primary) | Equipment name | "Canon EOS 5D Mark IV" |
| `SKU` | Single Line Text | Internal tracking code | "CAM-001" |
| `Category` | Single Select | Equipment type | "Camera" |
| `Total Quantity` | Number | Total owned units | 8 |
| `Daily Rate` | Currency | Rental rate per day | $45.00 |
| `Maintenance Status` | Single Select | Operational, Under Maintenance | "Operational" |
| `Allocations` | Linked Records | → Allocations table | [SCN-001-Canon...] |

**Example Record:**
```json
{
  "asset_name": "Canon EOS 5D Mark IV",
  "sku": "CAM-001",
  "category": "Camera",
  "total_quantity": 8,
  "daily_rate": 45.00,
  "maintenance_status": "Operational",
  "record_id": "recABC123"
}
```

**Demo Data (16 assets):**
- Cameras: Canon 5D Mark IV (8), Sony PXW-FS7 (3), GoPro HERO10 (4)
- Audio: Shure SM7B Mic (12), Yamaha Mixer (4), Sennheiser EW 112P (9), JBL Speakers (6)
- Drones: DJI Mavic Air 2 (5)
- Other: MacBook Pro (10), Dell Monitor (6), Epson Projector (7), etc.

#### Table 2: "Allocations"

**Table Structure:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `Allocation ID` | Single Line Text (Primary) | Unique identifier | "SCN-001-Canon EOS 5D Mark IV" |
| `Asset Link` | Linked Records | → Assets table | ["Canon EOS 5D Mark IV"] |
| `Scene Ref` | Single Line Text | Scene identifier from Notion | "SCN-001" |
| `Start Date` | Date | Reservation date | "2024-07-01" |
| `Quantity Reserved` | Number | Units reserved | 5 |
| `Status` | Single Select | Confirmed, Pending, Cancelled | "Confirmed" |

**Example Record:**
```json
{
  "allocation_id": "SCN-001-Canon EOS 5D Mark IV",
  "asset_link": ["recABC123"],
  "scene_ref": "SCN-001",
  "start_date": "2024-07-01",
  "quantity_reserved": 5,
  "status": "Confirmed"
}
```

**Demo Data (12 existing reservations):**
- Mix of Confirmed, Pending, and Cancelled reservations
- Dates range from July 2024
- Used to test availability calculations

---

### Data Relationships

```
┌─────────────────────────────────────────────────────────┐
│                    NOTION DATABASE                       │
│                   "Shooting Schedule"                    │
├─────────────────────────────────────────────────────────┤
│  Scene 15 (Scene Number = "Scene 15")                   │
│  ├─ Shoot Date: 2025-12-08                              │
│  ├─ Logistics Status: "Draft" → "Reserved" (updated)    │
│  ├─ Est. Budget: null → $XXX (calculated)               │
│  └─ Script Breakdown: "...DJI Mavic drone...4 GoPros"   │
└─────────────────────────────────────────────────────────┘
                          │
                          │ create_reservation updates
                          ↓
┌─────────────────────────────────────────────────────────┐
│              AIRTABLE: "Allocations"                    │
├─────────────────────────────────────────────────────────┤
│  New Record Created:                                    │
│  ├─ Scene Ref: "Scene 15"  ←─────────────────┐          │
│  ├─ Start Date: "2025-12-08"                 │          │
│  ├─ Quantity Reserved: 4                     │          │
│  ├─ Status: "Confirmed"                      │          │
│  └─ Asset Link: [recXYZ] ──────┐             │          │
└─────────────────────────────────┼─────────────┼─────────┘
                                  │             │
                        Linked Record     Scene Reference
                                  │             │
                                  ↓             │
┌─────────────────────────────────────────────────────────┐
│               AIRTABLE: "Assets"                        │
├─────────────────────────────────────────────────────────┤
│  GoPro HERO10 Black (recXYZ)                            │
│  ├─ Total Quantity: 4                                   │
│  ├─ Daily Rate: $25.00                                  │
│  ├─ Category: "Camera"                                  │
│  └─ Allocations: [..., recABC] (linked back)            │
└─────────────────────────────────────────────────────────┘
```

**Availability Calculation:**
```
Available = Total Quantity - SUM(Quantity Reserved WHERE Start Date = shoot_date AND Status IN ['Confirmed', 'Pending'])
```

**Example:**
- GoPro HERO10 Black: Total = 4
- Existing reservation on 2025-12-08: 0
- Scene 15 requests: 4
- Available: 4 - 0 = 4 ✓ (Can reserve)

---

### Tool → Data Mapping

| Tool | Reads From | Writes To | Key Fields |
|------|------------|-----------|------------|
| `get_schedule` | Notion Scenes | - | scene_id, scene_number, shoot_date, script_breakdown |
| `search_inventory` | Airtable Assets | - | asset_name, total_quantity, daily_rate |
| `check_availability` | Airtable Assets + Allocations | - | total_quantity, reserved (calculated) |
| `create_reservation` | Airtable Assets | Airtable Allocations + Notion Scenes | Creates allocation, updates logistics_status + est_budget |

## Tools (7 Total)

### Data Tools - `skills/data.py`

| Tool | Connection | Purpose |
|------|------------|---------|
| `get_schedule` | Notion | Fetch upcoming scenes with script breakdown |
| `search_inventory` | Airtable | Fuzzy search assets by name |
| `check_availability` | Airtable | Check real-time availability for date |
| `create_reservation` | Notion + Airtable | Create allocation and update scene status |

### Communication Tools - `skills/communications.py`

| Tool | Connection | Purpose |
|------|------------|---------|
| `post_briefing` | Slack | Post formatted summary to channel |
| `send_approval_request` | Slack | Send interactive approval buttons |
| `place_order` | None | Execute mock procurement order |

---

## Python Tool Development

### Pydantic BaseModel Pattern

```python
from pydantic import BaseModel, Field
from typing import Optional

class MyInput(BaseModel):
    """Input for my_tool."""
    required_field: str = Field(..., description="Required field")
    optional_field: int = Field(default=10, ge=1, le=100)

class MyOutput(BaseModel):
    """Output from my_tool."""
    result: str
    status: str  # Always: "success" or "error"
    error: Optional[str] = None
```

### Tool Decorator

```python
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from ibm_watsonx_orchestrate.agent_builder.connections import ConnectionType

@tool(
    expected_credentials=[
        {"app_id": "gcsc_notion_api", "type": ConnectionType.KEY_VALUE}
    ],
    permission=ToolPermission.READ_ONLY,
    description="Clear description of what the tool does"
)
def my_tool(input: MyInput) -> MyOutput:
    ...
```

---

## Accessing Connections

### KEY_VALUE Connections (Notion, Airtable, Slack)

```python
from ibm_watsonx_orchestrate.run import connections

notion_conn = connections.key_value("gcsc_notion_api")
token = notion_conn.get('token')
database_id = notion_conn.get('database_id')

slack_conn = connections.key_value("gcsc_slack_api")
slack_client = WebClient(token=slack_conn.get('token'))
channel_id = slack_conn.get('channel_id')
```

---

## Project Structure

```
orchestrate/
├── skills/
│   ├── data.py              # 4 data tools (Notion + Airtable)
│   └── communications.py    # 3 communication tools (Slack)
├── agents/
│   └── data_coordinator.yaml # Data Coordinator agent (YAML/CLI)
├── connections/
│   ├── notion_connection.yaml
│   ├── airtable_connection.yaml
│   └── slack_connection.yaml
├── collaborator.md          # Guide for creating Production Assistant (UI)
├── import-all.sh            # Deploy everything
└── remove-all.sh            # Cleanup
```

## Connections

| Connection | Type | Access Pattern |
|------------|------|----------------|
| `gcsc_notion_api` | key_value | `.get('token')`, `.get('database_id')` |
| `gcsc_airtable_api` | key_value | `.get('token')`, `.get('base_id')` |
| `gcsc_slack_api` | key_value | `.get('token')`, `.get('channel_id')` |
| `gcsc_google_ai` | key_value | `.get('api_key')` |

---

## CLI Commands Reference

### Deploy

```bash
./import-all.sh
```

### Test Agents

```bash
orchestrate chat start gcsc_DataCoordinator
orchestrate chat start gcsc_ProductionAssistant
```

### Cleanup

```bash
./remove-all.sh
```

### Manual Commands

```bash
# Import tools with connections
orchestrate tools import -k python \
  -f skills/data.py \
  -r requirements.txt \
  -a gcsc_notion_api \
  -a gcsc_airtable_api

# Import agent
orchestrate agents import --file agents/data_coordinator.yaml

# List resources
orchestrate agents list
orchestrate tools list
orchestrate connections list

# Set credentials
orchestrate connections set-credentials --app-id gcsc_slack_api --env draft \
  -e "token=$SLACK_BOT_TOKEN" \
  -e "channel_id=$SLACK_CHANNEL_ID"

orchestrate connections set-credentials --app-id gcsc_notion_api --env draft \
  -e "token=$NOTION_TOKEN" \
  -e "database_id=$NOTION_DATABASE_UUID"
```

---

## Reference Documentation

- **Workshop Setup**: [README.md](README.md)
- **UI Agent Creation**: [collaborator.md](collaborator.md)
- **ADK Docs**: [api_docs/orchestrate_adk.md](api_docs/orchestrate_adk.md)
- **CLI Reference**: [api_docs/orchestrate_cli.md](api_docs/orchestrate_cli.md)
