#!/usr/bin/env python3
"""
Cost tracking for Twelve Labs API usage
"""

import json
import time
from datetime import datetime
from pathlib import Path


class CostTracker:
    def __init__(self, log_file="cost_log.json"):
        self.log_file = log_file
        self.costs = self.load_costs()

    def load_costs(self):
        """Load existing cost data"""
        if Path(self.log_file).exists():
            with open(self.log_file, 'r') as f:
                return json.load(f)
        return {
            "total_cost": 0.0,
            "video_processing_cost": 0.0,
            "search_cost": 0.0,
            "sessions": []
        }

    def save_costs(self):
        """Save cost data to file"""
        with open(self.log_file, 'w') as f:
            json.dump(self.costs, f, indent=2)

    def log_video_processing(self, video_count, total_duration_minutes):
        """Log video processing costs"""
        cost_per_minute = 0.0015
        session_cost = total_duration_minutes * cost_per_minute

        session = {
            "timestamp": datetime.now().isoformat(),
            "type": "video_processing",
            "video_count": video_count,
            "duration_minutes": total_duration_minutes,
            "cost_per_minute": cost_per_minute,
            "session_cost": session_cost
        }

        self.costs["video_processing_cost"] += session_cost
        self.costs["total_cost"] += session_cost
        self.costs["sessions"].append(session)
        self.save_costs()

        print(f"💰 Video processing cost: ${session_cost:.4f}")
        print(f"📊 Total cost so far: ${self.costs['total_cost']:.4f}")

    def log_search_query(self, query_count=1):
        """Log search query costs (negligible but tracked)"""
        cost_per_query = 0.001  # Estimated minimal cost
        session_cost = query_count * cost_per_query

        session = {
            "timestamp": datetime.now().isoformat(),
            "type": "search_queries",
            "query_count": query_count,
            "cost_per_query": cost_per_query,
            "session_cost": session_cost
        }

        self.costs["search_cost"] += session_cost
        self.costs["total_cost"] += session_cost
        self.costs["sessions"].append(session)
        self.save_costs()

    def get_summary(self):
        """Get cost summary"""
        return {
            "total_cost": self.costs["total_cost"],
            "video_processing": self.costs["video_processing_cost"],
            "search_queries": self.costs["search_cost"],
            "budget_remaining": 100.0 - self.costs["total_cost"],
            "session_count": len(self.costs["sessions"])
        }

    def print_summary(self):
        """Print formatted cost summary"""
        summary = self.get_summary()

        print("\n" + "="*50)
        print("💰 COST TRACKER SUMMARY")
        print("="*50)
        print(f"Video Processing:    ${summary['video_processing']:.4f}")
        print(f"Search Queries:      ${summary['search_queries']:.4f}")
        print("-" * 30)
        print(f"Total Cost:          ${summary['total_cost']:.4f}")
        print(f"Budget ($100):       ${100.0:.2f}")
        print(f"Remaining:           ${summary['budget_remaining']:.2f}")
        print(f"Budget Used:         {(summary['total_cost']/100.0)*100:.2f}%")
        print("="*50)

        if summary['total_cost'] > 100.0:
            print("⚠️  WARNING: Budget exceeded!")
        elif summary['total_cost'] > 80.0:
            print("⚠️  WARNING: Approaching budget limit!")
        else:
            print("✅ Within budget")


def estimate_poc_cost():
    """Estimate total POC cost"""
    print("🧮 POC COST ESTIMATION")
    print("="*30)

    # Video processing
    video_count = 5
    duration_per_video = 15  # seconds
    total_minutes = (video_count * duration_per_video) / 60
    video_cost = total_minutes * 0.0015

    # Search queries (estimated)
    query_count = 50  # estimated for testing
    search_cost = query_count * 0.001

    # Infrastructure (free/local)
    infrastructure_cost = 0.0

    total_estimated = video_cost + search_cost + infrastructure_cost

    print(f"Videos ({video_count} × {duration_per_video}s): ${video_cost:.4f}")
    print(f"Search queries ({query_count}):     ${search_cost:.4f}")
    print(f"Infrastructure (local):   ${infrastructure_cost:.2f}")
    print("-" * 25)
    print(f"Total Estimated:          ${total_estimated:.4f}")
    print(f"Target Budget:            $100.00")
    print(f"Safety Margin:            ${100.0 - total_estimated:.2f}")

    return total_estimated


if __name__ == "__main__":
    tracker = CostTracker()

    print("Select an option:")
    print("1. Estimate POC cost")
    print("2. View current summary")
    print("3. Log video processing")
    print("4. Log search queries")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        estimate_poc_cost()
    elif choice == "2":
        tracker.print_summary()
    elif choice == "3":
        video_count = int(input("Number of videos processed: "))
        duration = float(input("Total duration (minutes): "))
        tracker.log_video_processing(video_count, duration)
    elif choice == "4":
        query_count = int(input("Number of search queries: "))
        tracker.log_search_query(query_count)
    else:
        print("Invalid choice")