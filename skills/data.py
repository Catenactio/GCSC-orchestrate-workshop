"""
Data Skills - Notion and Airtable operations for film production

Tools:
- get_schedule: Fetch upcoming scenes from Notion
- search_inventory: Fuzzy search assets in Airtable
- check_availability: Check real-time availability for asset/date
- create_reservation: Create allocation and update scene status
"""
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
from notion_client import Client as NotionClient
from pyairtable import Api as AirtableApi
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from ibm_watsonx_orchestrate.agent_builder.connections import ConnectionType
from ibm_watsonx_orchestrate.run import connections


# =============================================================================
# Pydantic Models
# =============================================================================

# --- get_schedule ---
class ScheduleInput(BaseModel):
    """Input for get_schedule tool."""
    days_ahead: int = Field(
        default=2,
        ge=1,
        le=30,
        description="Number of days ahead to fetch (default: 2)"
    )


class SceneData(BaseModel):
    """Data for a single scene from Notion."""
    scene_id: str
    scene_number: str
    shoot_date: str
    script_breakdown: str = Field(
        default="",
        description="Unstructured text describing equipment needs"
    )
    est_budget: Optional[float] = None
    logistics_status: str = "Pending"


class ScheduleOutput(BaseModel):
    """Output from get_schedule tool."""
    scenes: list[SceneData] = Field(default_factory=list)
    date_range: dict[str, str] = Field(default_factory=dict)
    total_scenes: int = 0
    status: str
    error: Optional[str] = None


# --- search_inventory ---
class SearchInput(BaseModel):
    """Input for search_inventory tool."""
    query: str = Field(
        ...,
        min_length=1,
        description="Search term to match against Asset Name"
    )
    max_results: int = Field(default=10, ge=1, le=50)


class AssetData(BaseModel):
    """Data for a single asset from Airtable."""
    asset_name: str
    total_quantity: int = 0
    daily_rate: float = 0.0
    category: str = "N/A"
    maintenance_status: str = "Unknown"
    record_id: Optional[str] = None


class SearchOutput(BaseModel):
    """Output from search_inventory tool."""
    assets: list[AssetData] = Field(default_factory=list)
    query: str
    items_found: int = 0
    status: str
    error: Optional[str] = None


# --- check_availability ---
class AvailabilityInput(BaseModel):
    """Input for check_availability tool."""
    asset_name: str = Field(..., description="Exact asset name to check")
    shoot_date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")


class AvailabilityOutput(BaseModel):
    """Output from check_availability tool."""
    asset_name: str
    shoot_date: str
    total_owned: int = 0
    reserved_on_date: int = 0
    available: int = 0
    daily_rate: float = 0.0
    is_available: bool = False
    asset_found: bool = False
    status: str
    error: Optional[str] = None


# --- create_reservation ---
class ReservationInput(BaseModel):
    """Input for create_reservation tool."""
    asset_name: str = Field(..., description="Asset to reserve")
    scene_id: str = Field(..., description="Notion page ID for the scene")
    scene_number: str = Field(..., description="Scene identifier (e.g., Scene 12)")
    shoot_date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    quantity: int = Field(..., ge=1, description="Number of units to reserve")


class ReservationOutput(BaseModel):
    """Output from create_reservation tool."""
    reservation_created: bool
    allocation_id: Optional[str] = None
    asset_name: str
    scene_number: str
    shoot_date: str
    quantity: int
    daily_rate: float = 0.0
    total_cost: float = 0.0
    scene_status_updated: bool = False
    status: str
    error: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================

def _extract_rich_text(field: dict) -> str:
    """Extract plain text from Notion rich_text field."""
    if not field or field.get("type") != "rich_text":
        return ""
    rich_text_list = field.get("rich_text", [])
    return "".join([block.get("plain_text", "") for block in rich_text_list])


def _extract_select(field: dict, default: str = "") -> str:
    """Extract value from Notion select field."""
    if not field or field.get("type") != "select":
        return default
    select_value = field.get("select")
    if select_value is None:
        return default
    return select_value.get("name", default)


# =============================================================================
# Tools
# =============================================================================

@tool(
    expected_credentials=[
        {"app_id": "gcsc_notion_api", "type": ConnectionType.KEY_VALUE}
    ],
    permission=ToolPermission.READ_ONLY,
    description=(
        "Fetches upcoming filming scenes from Notion. Parameter: 'days_ahead' (integer, "
        "1-30, default=2) - number of days to look ahead. Returns scene details including "
        "scene_id, scene_number, shoot_date (YYYY-MM-DD), and script_breakdown text "
        "describing equipment needs. Example: days_ahead=7 fetches scenes for next week."
    )
)
def get_schedule(input: ScheduleInput) -> ScheduleOutput:
    """
    Retrieves the shooting schedule from Notion for upcoming scenes.
    """
    days_ahead = input.days_ahead

    notion_conn = connections.key_value("gcsc_notion_api")
    notion = NotionClient(auth=notion_conn.get('token'))
    database_id = notion_conn.get('database_id')

    today = datetime.now().date()
    end_date = today + timedelta(days=days_ahead)

    try:
        response = notion.data_sources.query(
            **{
                "data_source_id": database_id,
                "filter": {
                    "and": [
                        {"property": "Shoot Date", "date": {"on_or_after": today.isoformat()}},
                        {"property": "Shoot Date", "date": {"on_or_before": end_date.isoformat()}}
                    ]
                },
                "sorts": [{"property": "Shoot Date", "direction": "ascending"}]
            }
        )

        scenes = []
        for page in response.get("results", []):
            props = page["properties"]
            scenes.append(SceneData(
                scene_id=page["id"],
                scene_number=props.get("Scene Number", {}).get("title", [{}])[0].get("plain_text", "N/A"),
                shoot_date=props.get("Shoot Date", {}).get("date", {}).get("start", "Unknown"),
                script_breakdown=_extract_rich_text(props.get("Script Breakdown", {})),
                est_budget=props.get("Est. Budget", {}).get("number"),
                logistics_status=_extract_select(props.get("Logistics Status", {}), "Pending")
            ))

        return ScheduleOutput(
            scenes=scenes,
            date_range={"start": today.isoformat(), "end": end_date.isoformat()},
            total_scenes=len(scenes),
            status="success"
        )

    except Exception as e:
        return ScheduleOutput(
            date_range={"start": today.isoformat(), "end": end_date.isoformat()},
            status="error",
            error=str(e)
        )


@tool(
    expected_credentials=[
        {"app_id": "gcsc_airtable_api", "type": ConnectionType.KEY_VALUE}
    ],
    permission=ToolPermission.READ_ONLY,
    description=(
        "Searches Airtable inventory for assets by name using fuzzy matching. "
        "Parameters: 'query' (string, required) - search term to match against asset names, "
        "'max_results' (integer, 1-50, default=10) - limit results. Returns asset_name, "
        "total_quantity, daily_rate, category. Example: query='Canon' finds all Canon equipment."
    )
)
def search_inventory(input: SearchInput) -> SearchOutput:
    """
    Searches Airtable inventory for items matching the query string.
    """
    query = input.query.strip()
    max_results = input.max_results

    airtable_conn = connections.key_value("gcsc_airtable_api")
    airtable_api = AirtableApi(airtable_conn.get('token'))
    base_id = airtable_conn.get('base_id')

    try:
        table = airtable_api.table(base_id, "Assets")
        escaped_query = query.replace("'", "\\'")
        formula = f"FIND(LOWER('{escaped_query}'), LOWER({{Asset Name}})) > 0"

        records = table.all(formula=formula, max_records=max_results, sort=["Asset Name"])

        assets = []
        for record in records:
            fields = record["fields"]
            assets.append(AssetData(
                asset_name=fields.get("Asset Name", "Unknown"),
                total_quantity=fields.get("Total Quantity", 0),
                daily_rate=fields.get("Daily Rate", 0.0),
                category=fields.get("Category", "N/A"),
                maintenance_status=fields.get("Maintenance Status", "Unknown"),
                record_id=record["id"]
            ))

        return SearchOutput(
            assets=assets,
            query=query,
            items_found=len(assets),
            status="success"
        )

    except Exception as e:
        return SearchOutput(query=query, status="error", error=str(e))


@tool(
    expected_credentials=[
        {"app_id": "gcsc_airtable_api", "type": ConnectionType.KEY_VALUE}
    ],
    permission=ToolPermission.READ_ONLY,
    description=(
        "Checks real-time availability of an asset for a specific shoot date by querying "
        "Airtable reservations. Parameters: 'asset_name' (string, required) - exact asset "
        "name as it appears in inventory, 'shoot_date' (string, required) - date in "
        "YYYY-MM-DD format. Returns: total_owned, reserved_on_date, available count, and "
        "daily_rate. Example: asset_name='Canon EOS 5D Mark IV', shoot_date='2025-12-10'."
    )
)
def check_availability(input: AvailabilityInput) -> AvailabilityOutput:
    """
    Determines available quantity of an asset for a specific date.
    Formula: available = total_owned - sum(reservations on date)
    """
    asset_name = input.asset_name.strip()
    shoot_date = input.shoot_date

    airtable_conn = connections.key_value("gcsc_airtable_api")
    airtable_api = AirtableApi(airtable_conn.get('token'))
    base_id = airtable_conn.get('base_id')

    try:
        # Get asset info
        assets_table = airtable_api.table(base_id, "Assets")
        escaped_name = asset_name.replace("'", "\\'")
        asset_records = assets_table.all(formula=f"{{Asset Name}}='{escaped_name}'", max_records=1)

        if not asset_records:
            return AvailabilityOutput(
                asset_name=asset_name,
                shoot_date=shoot_date,
                asset_found=False,
                status="success",
                error=f"Asset '{asset_name}' not found"
            )

        asset_fields = asset_records[0]["fields"]
        asset_record_id = asset_records[0]["id"]
        total_owned = asset_fields.get("Total Quantity", 0)
        daily_rate = asset_fields.get("Daily Rate", 0.0)

        # Get allocations for this date
        allocations_table = airtable_api.table(base_id, "Allocations")
        allocation_formula = (
            f"AND("
            f"FIND('{asset_record_id}', ARRAYJOIN({{Asset Link}})),"
            f"{{Start Date}}='{shoot_date}',"
            f"OR({{Status}}='Confirmed',{{Status}}='Pending')"
            f")"
        )
        allocation_records = allocations_table.all(formula=allocation_formula)

        reserved = sum(r["fields"].get("Quantity Reserved", 0) for r in allocation_records)
        available = total_owned - reserved

        return AvailabilityOutput(
            asset_name=asset_name,
            shoot_date=shoot_date,
            total_owned=total_owned,
            reserved_on_date=reserved,
            available=available,
            daily_rate=daily_rate,
            is_available=(available > 0),
            asset_found=True,
            status="success"
        )

    except Exception as e:
        return AvailabilityOutput(
            asset_name=asset_name,
            shoot_date=shoot_date,
            status="error",
            error=str(e)
        )


@tool(
    expected_credentials=[
        {"app_id": "gcsc_airtable_api", "type": ConnectionType.KEY_VALUE},
        {"app_id": "gcsc_notion_api", "type": ConnectionType.KEY_VALUE}
    ],
    description=(
        "Creates a reservation for an asset in Airtable and updates scene status in Notion. "
        "Parameters: 'asset_name' (string, exact name), 'scene_id' (string, Notion page ID), "
        "'scene_number' (string, e.g., 'Scene 15'), 'shoot_date' (string, YYYY-MM-DD format), "
        "'quantity' (integer, >=1, units to reserve). Creates allocation record with status "
        "'Confirmed' and updates scene logistics_status to 'Reserved'. Returns allocation_id "
        "and total_cost."
    )
)
def create_reservation(input: ReservationInput) -> ReservationOutput:
    """
    Creates an allocation record in Airtable and updates scene status in Notion.
    """
    asset_name = input.asset_name.strip()
    scene_id = input.scene_id
    scene_number = input.scene_number
    shoot_date = input.shoot_date
    quantity = input.quantity

    airtable_conn = connections.key_value("gcsc_airtable_api")
    airtable_api = AirtableApi(airtable_conn.get('token'))
    base_id = airtable_conn.get('base_id')

    notion_conn = connections.key_value("gcsc_notion_api")
    notion = NotionClient(auth=notion_conn.get('token'))

    try:
        # Step 1: Look up asset record ID
        assets_table = airtable_api.table(base_id, "Assets")
        escaped_name = asset_name.replace("'", "\\'")
        asset_records = assets_table.all(formula=f"{{Asset Name}}='{escaped_name}'", max_records=1)

        if not asset_records:
            return ReservationOutput(
                reservation_created=False,
                asset_name=asset_name,
                scene_number=scene_number,
                shoot_date=shoot_date,
                quantity=quantity,
                status="error",
                error=f"Asset '{asset_name}' not found"
            )

        asset_record_id = asset_records[0]["id"]
        daily_rate = asset_records[0]["fields"].get("Daily Rate", 0.0)
        total_cost = daily_rate * quantity

        # Step 2: Create allocation in Airtable
        allocations_table = airtable_api.table(base_id, "Allocations")
        new_record = allocations_table.create({
            "Asset Link": [asset_record_id],
            "Scene Ref": scene_number,
            "Start Date": shoot_date,
            "Quantity Reserved": quantity,
            "Status": "Confirmed"
        })

        # Step 3: Update scene status in Notion
        scene_updated = False
        try:
            notion.pages.update(
                page_id=scene_id,
                properties={
                    "Logistics Status": {"select": {"name": "Reserved"}},
                    "Est. Budget": {"number": total_cost}
                }
            )
            scene_updated = True
        except Exception:
            pass  # Continue even if Notion update fails

        return ReservationOutput(
            reservation_created=True,
            allocation_id=new_record["id"],
            asset_name=asset_name,
            scene_number=scene_number,
            shoot_date=shoot_date,
            quantity=quantity,
            daily_rate=daily_rate,
            total_cost=total_cost,
            scene_status_updated=scene_updated,
            status="success"
        )

    except Exception as e:
        return ReservationOutput(
            reservation_created=False,
            asset_name=asset_name,
            scene_number=scene_number,
            shoot_date=shoot_date,
            quantity=quantity,
            status="error",
            error=str(e)
        )
