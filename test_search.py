#!/usr/bin/env python3
"""
Test script for Twelve Labs API search functionality
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.embeddings.twelve_labs_client import TwelveLabsClient
from config.settings import EMBEDDINGS_FILE

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_search")


def load_index_id():
    """Load the index ID from embeddings file"""
    try:
        with open(EMBEDDINGS_FILE, 'r') as f:
            data = json.load(f)
            index_id = data.get("index_id")
            if not index_id:
                logger.error(f"No index_id found in {EMBEDDINGS_FILE}")
                return None
            logger.info(f"Loaded index_id: {index_id}")
            return index_id
    except FileNotFoundError:
        logger.error(f"Embeddings file not found: {EMBEDDINGS_FILE}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in embeddings file: {EMBEDDINGS_FILE}")
        return None


def test_search(query="pepsi can", options=None):
    """Test search functionality"""
    logger.info(f"Testing search with query: '{query}'")
    
    # Load the index ID
    # index_id = load_index_id()
    index_id = "68c84ff6707c44d8e8db8c16"
    if not index_id:
        logger.error("Cannot proceed without an index ID")
        return False
    
    # Create a client
    logger.info("Creating Twelve Labs client")
    client = TwelveLabsClient()
    
    # Default search options
    if options is None:
        options = {
            "search_options": ["visual", "audio"],
            "threshold": "medium",
            "operator": "or",
            "page_limit": 2,
            "adjust_confidence_level": 0.5,
            "group_by": "video"
        }
    
    logger.info(f"Search options: {options}")
    
    # Execute the search
    logger.info(f"Executing search on index {index_id}")
    result = client.search_text(
        index_id=index_id,
        query=query,
        options=options
    )
    
    # Check if the search was successful
    if not result["success"]:
        logger.error(f"Search failed: {result['error']}")
        return False
    
    # Log the search results
    search_data = result["data"]
    logger.info(f"Search result data structure: {list(search_data.keys()) if isinstance(search_data, dict) else type(search_data)}")
    
    # Process search results
    results = search_data.get("data", [])
    logger.info(f"Number of search results: {len(results)}")
    
    # Print the search results
    print("\n=== SEARCH RESULTS ===")
    print(f"Query: '{query}'")
    print(f"Total results: {len(results)}")
    print("=" * 50)
    
    for i, item in enumerate(results):
        print(f"\nResult #{i+1}:")
        video_id = item.get("video_id", "N/A")
        confidence = item.get("confidence", 0.0)
        score = item.get("score", 0.0)
        start = item.get("start", 0.0)
        end = item.get("end", 0.0)
        metadata = item.get("metadata", {})
        filename = metadata.get("filename", "unknown") if isinstance(metadata, dict) else "unknown"
        clip_text = item.get("clip_text", "")
        
        print(f"  Video ID: {video_id}")
        print(f"  Filename: {filename}")
        print(f"  Confidence: {confidence}")
        # Check if score is a number or a string
        if isinstance(score, (int, float)):
            print(f"  Score: {score:.4f}")
        else:
            print(f"  Score: {score}")
        # Check if start and end are numbers or strings
        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
            print(f"  Time Range: {start:.2f}s - {end:.2f}s")
        else:
            print(f"  Time Range: {start}s - {end}s")
        if clip_text:
            print(f"  Text: {clip_text}")
        print("-" * 40)
    
    # Print the raw JSON output for debugging
    print("\n=== RAW JSON OUTPUT ===")
    print(json.dumps(result, indent=2, default=str))
    
    return True


def test_clip_access(video_id, start_time, end_time):
    """Test accessing a specific clip"""
    logger.info(f"Testing clip access for video_id: {video_id}, time range: {start_time}-{end_time}")
    
    # Create a client
    client = TwelveLabsClient()
    
    # Get video info
    video_info = client.get_video_info(video_id)
    if not video_info["success"]:
        logger.error(f"Failed to get video info: {video_info['error']}")
        return False
    
    logger.info(f"Video info: {video_info['data']}")
    print("\n=== VIDEO INFO ===")
    print(json.dumps(video_info["data"], indent=2, default=str))
    
    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Test Twelve Labs API search functionality')
    parser.add_argument('query', type=str, help='Search query text')
    parser.add_argument('--video-id', type=str, help='Video ID for clip access test')
    parser.add_argument('--start', type=float, default=0.0, help='Clip start time in seconds')
    parser.add_argument('--end', type=float, default=10.0, help='Clip end time in seconds')
    
    args = parser.parse_args()
    
    print("Twelve Labs API Search Test")
    print("=" * 50)
    
    if args.video_id:
        test_clip_access(args.video_id, args.start, args.end)
    else:
        test_search(args.query)


if __name__ == "__main__":
    main()