#!/usr/bin/env python3
"""
Generate embeddings for videos using Twelve Labs API
"""

import os
import json
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.embeddings.twelve_labs_client import TwelveLabsClient
from config.settings import VIDEO_DATA_DIR, EMBEDDINGS_FILE


class EmbeddingGenerator:
    def __init__(self):
        self.client = TwelveLabsClient()
        self.index_id = None
        self.embeddings_data = {
            "index_id": None,
            "videos": []
        }

    def get_video_files(self):
        """Get list of video files from data directory"""
        video_dir = Path(VIDEO_DATA_DIR)
        video_extensions = {'.mp4', '.mov', '.avi'}

        video_files = [
            f for f in video_dir.iterdir()
            if f.is_file() and f.suffix.lower() in video_extensions
        ]

        return sorted(video_files)

    def create_index(self):
        """Create a new index for the POC or use an existing one"""
        index_name = "semantic_video_search_poc"
        print(f"Looking for existing index with name '{index_name}'...")
        
        # Check if an index with this name already exists
        try:
            # Get list of existing indexes
            test_result = self.client.test_connection()
            if test_result["success"] and test_result["data"]:
                # Check if any index has the same name
                for index in test_result["data"]:
                    if hasattr(index, 'index_name') and index.index_name == index_name:
                        print(f"✅ Found existing index: {index.id}")
                        self.index_id = index.id
                        self.embeddings_data["index_id"] = self.index_id
                        return True
            
            # If we reach here, no matching index was found
            print(f"Creating new index '{index_name}'...")
            result = self.client.create_index(
                index_name=index_name,
                engines=["pegasus1.1", "marengo2.6"]
            )

            if result["success"]:
                self.index_id = result["data"]["_id"]
                self.embeddings_data["index_id"] = self.index_id
                print(f"✅ Index created: {self.index_id}")
                return True
            else:
                print(f"❌ Failed to create index: {result['error']}")
                return False
        except Exception as e:
            print(f"❌ Error checking/creating index: {str(e)}")
            return False

    def upload_video(self, video_path):
        """Upload a single video and wait for processing"""
        print(f"Uploading {video_path.name}...")

        # Upload the video
        result = self.client.upload_video(self.index_id, str(video_path))

        if not result["success"]:
            print(f"❌ Upload failed: {result['error']}")
            return None

        task_id = result["data"]["_id"]
        print(f"✅ Video uploaded with task ID: {task_id}")
        print("Waiting for processing...")

        # Wait for the task to complete
        wait_result = self.client.wait_for_task_completion(task_id)

        if not wait_result["success"]:
            print(f"❌ Video processing failed: {wait_result.get('error', 'Unknown error')}")
            return None

        # Get the video ID from the task completion result
        video_id = wait_result["data"]["video_id"]
        print(f"✅ Video processing completed. Video ID: {video_id}")

        video_data = {
            "video_id": video_id,
            "task_id": task_id,
            "filename": video_path.name,
            "filepath": str(video_path),
            "status": "ready"
        }

        return video_data

    def generate_embeddings(self):
        """Generate embeddings for all videos"""
        video_files = self.get_video_files()

        if not video_files:
            print("❌ No video files found in data/videos/")
            print("Please add 5 short video files (≤15s each)")
            return False

        print(f"Found {len(video_files)} video files")

        if not self.create_index():
            return False

        for video_file in video_files:
            print(f"\nProcessing {video_file.name}...")

            video_data = self.upload_video(video_file)
            if video_data:
                self.embeddings_data["videos"].append(video_data)
            else:
                print(f"❌ Skipping {video_file.name}")

        self.save_embeddings()
        print(f"\n✅ Generated embeddings for {len(self.embeddings_data['videos'])} videos")
        print(f"💾 Saved to {EMBEDDINGS_FILE}")

        return True

    def save_embeddings(self):
        """Save embeddings data to JSON file"""
        with open(EMBEDDINGS_FILE, 'w') as f:
            json.dump(self.embeddings_data, f, indent=2)

    def load_embeddings(self):
        """Load existing embeddings data"""
        if os.path.exists(EMBEDDINGS_FILE):
            with open(EMBEDDINGS_FILE, 'r') as f:
                self.embeddings_data = json.load(f)
            return True
        return False


def main():
    print("Twelve Labs Video Embedding Generator")
    print("=" * 40)

    generator = EmbeddingGenerator()

    if generator.load_embeddings():
        print("Found existing embeddings file")
        response = input("Regenerate embeddings? (y/N): ").strip().lower()
        if response != 'y':
            print("Using existing embeddings")
            return

    success = generator.generate_embeddings()

    if success:
        print("\n🎉 Embedding generation complete!")
        print("Next steps:")
        print("1. Run search API: python -m src.api.main")
        print("2. Start frontend: streamlit run src/frontend/app.py")
    else:
        print("\n❌ Embedding generation failed")
        print("Check your API key and video files")


if __name__ == "__main__":
    main()