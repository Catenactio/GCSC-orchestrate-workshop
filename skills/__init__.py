"""
Production Logistics Skills for IBM watsonx Orchestrate
Simplified two-agent workshop: Data tools and Communication tools
"""

from skills.data import (
    get_schedule,
    search_inventory,
    check_availability,
    create_reservation,
)

from skills.communications import (
    post_briefing,
    send_approval_request,
    place_order,
)

__all__ = [
    # Data tools
    "get_schedule",
    "search_inventory",
    "check_availability",
    "create_reservation",
    # Communication tools
    "post_briefing",
    "send_approval_request",
    "place_order",
]
