#!/usr/bin/env python3
"""
Test script for the Semantic Video Search API
"""

import requests
import json
import argparse
import sys
import time

def test_search_api(query="person walking", max_results=3, api_url="http://localhost:8000"):
    """Test the search API endpoint"""
    
    # First check if the API is running
    try:
        health_response = requests.get(f"{api_url}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"API health check failed with status code {health_response.status_code}")
            print(health_response.text)
            return False
        
        print("API health check successful")
        print(f"Health response: {health_response.json()}")
    except requests.exceptions.ConnectionError:
        print(f"Could not connect to API at {api_url}. Make sure the server is running.")
        return False
    
    # Make the search request
    search_url = f"{api_url}/search"
    payload = {"query": query, "max_results": max_results}
    
    print(f"\nSending search request to {search_url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        search_response = requests.post(
            search_url, 
            json=payload,
            timeout=10  # Increased timeout for search operation
        )
        
        # Print response status
        print(f"\nSearch response status: {search_response.status_code}")
        
        # If successful, print the results
        if search_response.status_code == 200:
            result = search_response.json()
            print(f"\nSearch Results for '{query}':")
            print(f"Total results: {result['total_results']}")
            
            for i, item in enumerate(result["results"]):
                print(f"\nResult #{i+1}:")
                print(f"  Video ID: {item['video_id']}")
                print(f"  Filename: {item['filename']}")
                print(f"  Confidence: {item['confidence']}")
                print(f"  Score: {item['score']}")
                print(f"  Time Range: {item['start']}s - {item['end']}s")
                if item.get("clip_text"):
                    print(f"  Text: {item['clip_text']}")
            
            # Print the raw response for debugging
            print("\nRaw Response:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"Search request failed with status code {search_response.status_code}")
            print(search_response.text)
            return False
    except Exception as e:
        print(f"Error making search request: {str(e)}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Test the Semantic Video Search API')
    parser.add_argument('--query', type=str, default="person walking", help='Search query text')
    parser.add_argument('--max', type=int, default=3, help='Maximum number of results')
    parser.add_argument('--url', type=str, default="http://localhost:8000", help='API base URL')
    parser.add_argument('--wait', type=int, default=0, help='Wait time in seconds before testing (useful if starting server separately)')
    
    args = parser.parse_args()
    
    # Wait if specified (to allow server to start)
    if args.wait > 0:
        print(f"Waiting {args.wait} seconds before testing...")
        time.sleep(args.wait)
    
    print("Semantic Video Search API Test")
    print("=" * 50)
    
    success = test_search_api(args.query, args.max, args.url)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()