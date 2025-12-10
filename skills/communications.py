"""
Communications Skills - Slack and procurement operations for film production

Tools:
- post_briefing: Post formatted summary to Slack
- send_approval_request: Send interactive approval buttons
- place_order: Execute mock procurement order
"""
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from ibm_watsonx_orchestrate.agent_builder.tools import tool
from ibm_watsonx_orchestrate.agent_builder.connections import ConnectionType
from ibm_watsonx_orchestrate.run import connections


# =============================================================================
# Pydantic Models
# =============================================================================

# --- post_briefing ---
class BriefingInput(BaseModel):
    """Input for post_briefing tool."""
    message: str = Field(..., description="Main briefing message to post")
    channel_id: Optional[str] = Field(
        default=None,
        description="Slack channel ID (optional - defaults to configured channel)"
    )


class BriefingOutput(BaseModel):
    """Output from post_briefing tool."""
    posted: bool
    message_ts: Optional[str] = None
    channel: Optional[str] = None
    status: str
    error: Optional[str] = None


# --- send_approval_request ---
class ApprovalInput(BaseModel):
    """Input for send_approval_request tool."""
    item_description: str = Field(..., description="What needs approval")
    total_cost: float = Field(..., ge=0, description="Total cost amount")
    scene_number: Optional[str] = Field(default=None, description="Scene reference")
    channel_id: Optional[str] = Field(
        default=None,
        description="Slack channel ID (optional - defaults to configured channel)"
    )


class ApprovalOutput(BaseModel):
    """Output from send_approval_request tool."""
    sent: bool
    message_ts: Optional[str] = None
    channel: Optional[str] = None
    item_description: str
    total_cost: float
    status: str
    error: Optional[str] = None


# --- place_order ---
class OrderInput(BaseModel):
    """Input for place_order tool."""
    item_name: str = Field(..., description="Item to order")
    quantity: int = Field(..., ge=1, description="Quantity to order")
    unit_cost: float = Field(..., ge=0, description="Cost per unit")
    scene_number: Optional[str] = Field(default=None, description="Scene reference")


class OrderOutput(BaseModel):
    """Output from place_order tool."""
    order_placed: bool
    order_id: Optional[str] = None
    item_name: str
    quantity: int
    total_cost: float
    vendor: str = "Production Supply Co."
    estimated_delivery: Optional[str] = None
    status: str
    error: Optional[str] = None


# =============================================================================
# Tools
# =============================================================================

@tool(
    expected_credentials=[
        {"app_id": "gcsc_slack_api", "type": ConnectionType.KEY_VALUE}
    ],
    description=(
        "Posts a briefing message to the production team Slack channel. Use this to send "
        "daily updates, equipment status summaries, or any team communication. "
        "Parameter: 'message' (string, required) - the briefing content to post. "
        "The channel is pre-configured - do NOT ask the user for a channel."
    )
)
def post_briefing(input: BriefingInput) -> BriefingOutput:
    """
    Sends a formatted briefing message to Slack.
    """
    slack_conn = connections.key_value("gcsc_slack_api")
    slack_client = WebClient(token=slack_conn.get('token'))

    message = input.message
    channel_id = input.channel_id or slack_conn.get('channel_id')

    try:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Production Update"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Posted by Production Assistant | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    }
                ]
            }
        ]

        response = slack_client.chat_postMessage(
            channel=channel_id,
            text=message,
            blocks=blocks
        )

        return BriefingOutput(
            posted=True,
            message_ts=response["ts"],
            channel=response["channel"],
            status="success"
        )

    except SlackApiError as e:
        return BriefingOutput(
            posted=False,
            status="error",
            error=str(e.response["error"])
        )


@tool(
    expected_credentials=[
        {"app_id": "gcsc_slack_api", "type": ConnectionType.KEY_VALUE}
    ],
    description=(
        "Sends an approval request to Slack with Approve/Deny buttons. Use this for "
        "purchases over $100 that need budget approval from the team. Parameters: "
        "'item_description' (string, required), 'total_cost' (number, required). "
        "Optional: 'scene_number' for context. The channel is pre-configured - "
        "do NOT ask the user for a channel."
    )
)
def send_approval_request(input: ApprovalInput) -> ApprovalOutput:
    """
    Sends a Slack message with approval buttons for budget items.
    """
    slack_conn = connections.key_value("gcsc_slack_api")
    slack_client = WebClient(token=slack_conn.get('token'))

    item_description = input.item_description
    total_cost = input.total_cost
    scene_number = input.scene_number
    channel_id = input.channel_id or slack_conn.get('channel_id')

    try:
        scene_text = f"\n*Scene:* {scene_number}" if scene_number else ""

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Approval Required"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Item:* {item_description}\n"
                        f"*Total Cost:* ${total_cost:.2f}"
                        f"{scene_text}\n"
                        f"*Requested by:* Production Assistant"
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
                        "value": f"approve_{item_description}",
                        "action_id": "approve_purchase"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Deny"},
                        "style": "danger",
                        "value": f"deny_{item_description}",
                        "action_id": "deny_purchase"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Approval threshold: $100 | Requested at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    }
                ]
            }
        ]

        response = slack_client.chat_postMessage(
            channel=channel_id,
            text=f"Approval needed: {item_description} (${total_cost:.2f})",
            blocks=blocks
        )

        return ApprovalOutput(
            sent=True,
            message_ts=response["ts"],
            channel=response["channel"],
            item_description=item_description,
            total_cost=total_cost,
            status="success"
        )

    except SlackApiError as e:
        return ApprovalOutput(
            sent=False,
            item_description=item_description,
            total_cost=total_cost,
            status="error",
            error=str(e.response["error"])
        )


@tool(
    description=(
        "Places a procurement order (mock). Use this after getting approval to "
        "execute the purchase. Returns an order ID and estimated delivery date."
    )
)
def place_order(input: OrderInput) -> OrderOutput:
    """
    Executes a procurement order (mock implementation).
    In production, this would integrate with a real vendor API.
    """
    item_name = input.item_name
    quantity = input.quantity
    unit_cost = input.unit_cost
    scene_number = input.scene_number

    try:
        # Generate mock order details
        order_id = f"PO-{datetime.now().strftime('%Y%m%d')}-{abs(hash(item_name)) % 10000:04d}"
        total_cost = unit_cost * quantity
        estimated_delivery = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

        return OrderOutput(
            order_placed=True,
            order_id=order_id,
            item_name=item_name,
            quantity=quantity,
            total_cost=total_cost,
            vendor="Production Supply Co.",
            estimated_delivery=estimated_delivery,
            status="success"
        )

    except Exception as e:
        return OrderOutput(
            order_placed=False,
            item_name=item_name,
            quantity=quantity,
            total_cost=unit_cost * quantity,
            status="error",
            error=str(e)
        )
