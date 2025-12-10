"""
Standalone test script for the simplified two-agent workshop tools

Tests the 7 tools:
- Data: get_schedule, search_inventory, check_availability, create_reservation
- Communications: post_briefing, send_approval_request, place_order
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notion_client import Client as NotionClient
from pyairtable import Api as AirtableApi
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load environment variables
load_dotenv('.env.credentials')


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60 + "\n")


def test_get_schedule():
    """Test get_schedule tool (Notion)"""
    print_section("TEST: get_schedule")

    token = os.getenv('NOTION_INTEGARTION_SECRET')
    database_id = os.getenv('NOTION_DATABASE_UUID')

    if not token or not database_id:
        print("Missing Notion credentials")
        return None

    notion = NotionClient(auth=token)
    today = datetime.now().date()
    end_date = today + timedelta(days=2)

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
            scene_number = props.get("Scene Number", {}).get("title", [{}])[0].get("plain_text", "N/A")
            shoot_date = props.get("Shoot Date", {}).get("date", {}).get("start", "Unknown")

            # Extract script breakdown
            breakdown_field = props.get("Script Breakdown", {})
            script_breakdown = ""
            if breakdown_field.get("type") == "rich_text":
                script_breakdown = "".join([t.get("plain_text", "") for t in breakdown_field.get("rich_text", [])])

            scenes.append({
                "scene_id": page["id"],
                "scene_number": scene_number,
                "shoot_date": shoot_date,
                "script_breakdown": script_breakdown
            })

        print(f"Found {len(scenes)} scenes")
        for scene in scenes:
            print(f"  {scene['scene_number']} - {scene['shoot_date']}")
            if scene['script_breakdown']:
                preview = scene['script_breakdown'][:80] + "..." if len(scene['script_breakdown']) > 80 else scene['script_breakdown']
                print(f"    Script: {preview}")

        return scenes

    except Exception as e:
        print(f"Error: {e}")
        return None


def test_search_inventory():
    """Test search_inventory tool (Airtable)"""
    print_section("TEST: search_inventory")

    token = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_INVENTORY_BASE_ID')

    if not token or not base_id:
        print("Missing Airtable credentials")
        return

    airtable_api = AirtableApi(token)
    table = airtable_api.table(base_id, "Assets")

    # Test searches
    test_queries = ["Canon", "Sony", "Microphone"]

    for query in test_queries:
        try:
            escaped = query.replace("'", "\\'")
            formula = f"FIND(LOWER('{escaped}'), LOWER({{Asset Name}})) > 0"
            records = table.all(formula=formula, max_records=5, sort=["Asset Name"])

            print(f"\nSearch: '{query}'")
            print(f"  Found {len(records)} items:")
            for record in records:
                fields = record["fields"]
                name = fields.get("Asset Name", "Unknown")
                qty = fields.get("Total Quantity", 0)
                rate = fields.get("Daily Rate", 0.0)
                print(f"    {name} - {qty} units @ ${rate}/day")

        except Exception as e:
            print(f"  Error: {e}")


def test_check_availability():
    """Test check_availability tool (Airtable)"""
    print_section("TEST: check_availability")

    token = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_INVENTORY_BASE_ID')

    if not token or not base_id:
        print("Missing Airtable credentials")
        return

    airtable_api = AirtableApi(token)
    assets_table = airtable_api.table(base_id, "Assets")
    allocations_table = airtable_api.table(base_id, "Allocations")

    # Test with a sample asset
    test_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    test_assets = ["Canon EOS 5D Mark IV", "Sony Venice"]

    for asset_name in test_assets:
        try:
            print(f"\nAsset: {asset_name} on {test_date}")

            # Get asset info
            escaped = asset_name.replace("'", "\\'")
            asset_records = assets_table.all(formula=f"{{Asset Name}}='{escaped}'", max_records=1)

            if not asset_records:
                print(f"  Not found in inventory")
                continue

            asset_record_id = asset_records[0]["id"]
            total_owned = asset_records[0]["fields"].get("Total Quantity", 0)
            daily_rate = asset_records[0]["fields"].get("Daily Rate", 0.0)

            # Check allocations
            alloc_formula = (
                f"AND("
                f"FIND('{asset_record_id}', ARRAYJOIN({{Asset Link}})),"
                f"{{Start Date}}='{test_date}',"
                f"OR({{Status}}='Confirmed',{{Status}}='Pending')"
                f")"
            )
            allocations = allocations_table.all(formula=alloc_formula)

            reserved = sum(a["fields"].get("Quantity Reserved", 0) for a in allocations)
            available = total_owned - reserved

            print(f"  Total owned: {total_owned}")
            print(f"  Reserved: {reserved}")
            print(f"  Available: {available}")
            print(f"  Daily rate: ${daily_rate}")
            print(f"  Status: {'✅ Available' if available > 0 else '❌ Not available'}")

        except Exception as e:
            print(f"  Error: {e}")


def test_create_reservation():
    """Test create_reservation tool (Airtable + Notion)"""
    print_section("TEST: create_reservation")

    airtable_token = os.getenv('AIRTABLE_API_KEY')
    airtable_base_id = os.getenv('AIRTABLE_INVENTORY_BASE_ID')
    notion_token = os.getenv('NOTION_INTEGARTION_SECRET')

    if not all([airtable_token, airtable_base_id, notion_token]):
        print("Missing credentials")
        return

    airtable_api = AirtableApi(airtable_token)
    assets_table = airtable_api.table(airtable_base_id, "Assets")
    allocations_table = airtable_api.table(airtable_base_id, "Allocations")

    try:
        # Get first asset for testing
        asset = assets_table.all(max_records=1)[0]
        asset_name = asset["fields"].get("Asset Name", "Unknown")
        asset_id = asset["id"]
        daily_rate = asset["fields"].get("Daily Rate", 0.0)

        print(f"Creating test reservation:")
        print(f"  Asset: {asset_name}")
        print(f"  Quantity: 1")
        print(f"  Date: {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}")

        # Create allocation
        allocation = allocations_table.create({
            "Asset Link": [asset_id],
            "Scene Ref": "TEST-SCENE",
            "Start Date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "Quantity Reserved": 1,
            "Status": "Confirmed"
        })

        print(f"  ✅ Allocation created: {allocation['id']}")
        print(f"  Cost: ${daily_rate * 1:.2f}")

        # Clean up
        allocations_table.delete(allocation['id'])
        print(f"  🗑️  Test allocation deleted")

    except Exception as e:
        print(f"  Error: {e}")


def test_post_briefing():
    """Test post_briefing tool (Slack)"""
    print_section("TEST: post_briefing")

    token = os.getenv('SLACK_BOT_TOKEN')
    channel_id = os.getenv('SLACK_CHANNEL_ID', 'C09UGCHJJUT')

    if not token:
        print("Missing SLACK_BOT_TOKEN")
        return

    slack_client = WebClient(token=token)

    message = (
        "📋 *Equipment Status Update*\n\n"
        "Scene 12 - December 9, 2025\n"
        "• Canon EOS 5D Mark IV (2 units) - ✅ Available\n"
        "• Sony Venice (1 unit) - ✅ Available\n\n"
        "Total estimated cost: $590.00"
    )

    try:
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Production Update"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message}
            },
            {
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f"Posted by Production Assistant | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                }]
            }
        ]

        response = slack_client.chat_postMessage(
            channel=channel_id,
            text=message,
            blocks=blocks
        )

        print(f"✅ Briefing posted to Slack")
        print(f"  Channel: {response['channel']}")
        print(f"  Timestamp: {response['ts']}")

    except SlackApiError as e:
        print(f"Error: {e.response['error']}")


def test_send_approval_request():
    """Test send_approval_request tool (Slack)"""
    print_section("TEST: send_approval_request")

    token = os.getenv('SLACK_BOT_TOKEN')
    channel_id = os.getenv('SLACK_CHANNEL_ID', 'C09UGCHJJUT')

    if not token:
        print("Missing SLACK_BOT_TOKEN")
        return

    slack_client = WebClient(token=token)

    try:
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Approval Required"}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Item:* Camera rental for Scene 12\n"
                        "*Total Cost:* $150.00\n"
                        "*Scene:* Scene 12\n"
                        "*Requested by:* Production Assistant"
                    )
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve"},
                        "style": "primary",
                        "value": "approve_test",
                        "action_id": "approve_purchase"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Deny"},
                        "style": "danger",
                        "value": "deny_test",
                        "action_id": "deny_purchase"
                    }
                ]
            }
        ]

        response = slack_client.chat_postMessage(
            channel=channel_id,
            text="Approval needed: Camera rental for Scene 12 ($150.00)",
            blocks=blocks
        )

        print(f"✅ Approval request sent")
        print(f"  Channel: {response['channel']}")
        print(f"  Timestamp: {response['ts']}")

    except SlackApiError as e:
        print(f"Error: {e.response['error']}")


def test_place_order():
    """Test place_order tool (mock)"""
    print_section("TEST: place_order")

    # Mock order details
    item_name = "Canon EOS 5D Mark IV"
    quantity = 2
    unit_cost = 45.00
    total_cost = unit_cost * quantity

    # Generate mock order ID
    order_id = f"PO-{datetime.now().strftime('%Y%m%d')}-{abs(hash(item_name)) % 10000:04d}"
    estimated_delivery = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

    print(f"Placing order:")
    print(f"  Item: {item_name}")
    print(f"  Quantity: {quantity}")
    print(f"  Unit cost: ${unit_cost}")
    print(f"  Total: ${total_cost}")
    print(f"\n✅ Order placed successfully!")
    print(f"  Order ID: {order_id}")
    print(f"  Vendor: Production Supply Co.")
    print(f"  Estimated delivery: {estimated_delivery}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎬 Standalone Test - Simplified Two-Agent Workshop")
    print("="*60)
    print("Testing 7 tools for the two-agent collaboration system")
    print("="*60)

    # Data Tools
    print("\n🔷 DATA TOOLS")
    scenes = test_get_schedule()
    test_search_inventory()
    test_check_availability()
    test_create_reservation()

    # Communication Tools
    print("\n🔷 COMMUNICATION TOOLS")
    test_post_briefing()
    test_send_approval_request()
    test_place_order()

    print("\n" + "="*60)
    print("✅ All tests complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Run ./import-all.sh to deploy tools")
    print("  2. Create Production Assistant in UI (see collaborator.md)")
    print("  3. Test: orchestrate chat start gcsc_ProductionAssistant")
    print()
