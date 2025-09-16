#!/usr/bin/env python3
"""
Test script to verify Twelve Labs API connectivity
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.embeddings.twelve_labs_client import TwelveLabsClient
from config.settings import TWELVE_LABS_API_KEY


def main():
    print("Testing Twelve Labs API Connection...")
    print("=" * 50)

    if not TWELVE_LABS_API_KEY:
        print("❌ ERROR: TWELVE_LABS_API_KEY not found!")
        print("Please:")
        print("1. Copy .env.example to .env")
        print("2. Add your Twelve Labs API key to .env")
        print("3. Get API key from: https://playground.twelvelabs.io/")
        return

    client = TwelveLabsClient()

    print(f"API Key: {TWELVE_LABS_API_KEY[:8]}..." if TWELVE_LABS_API_KEY else "None")
    print("Using official Twelve Labs SDK")
    print()

    result = client.test_connection()

    if result["success"]:
        print("✅ Connection successful!")
        indexes = result["data"]
        if indexes:
            print(f"Found {len(indexes)} existing indexes:")
            for index in indexes:
                print(f"  - {index.index_name} (ID: {getattr(index, 'id', 'unknown')})")
        else:
            print("No existing indexes found (this is normal for new accounts)")
    else:
        print("❌ Connection failed!")
        print(f"Error: {result['error']}")
        print("\nTroubleshooting:")
        print("1. Check your API key is correct")
        print("2. Verify your account has API access")
        print("3. Check internet connectivity")


if __name__ == "__main__":
    main()