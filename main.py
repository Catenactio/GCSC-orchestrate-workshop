"""
IBM watsonx Orchestrate ADK - Environment Validation
Validates environment variables for the Production Logistics Workshop
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """
    Validate environment configuration for the two-agent workshop.
    """
    print("Production Logistics Workshop - Environment Validation")
    print("=" * 60)
    print()

    # Required environment variables
    required_vars = [
        "NOTION_INTEGARTION_SECRET",
        "NOTION_DATABASE_UUID",
        "AIRTABLE_API_KEY",
        "AIRTABLE_INVENTORY_BASE_ID",
        "SLACK_BOT_TOKEN",
        "SLACK_CHANNEL_ID",
        "GOOGLE_API_KEY",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("Please configure these in .env.credentials")
        exit(1)

    print("Environment variables configured:")
    for var in required_vars:
        value = os.getenv(var)
        masked = value[:8] + "..." if value and len(value) > 8 else "***"
        print(f"   {var}: {masked}")

    print()
    print("=" * 60)
    print("Environment validation successful!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
