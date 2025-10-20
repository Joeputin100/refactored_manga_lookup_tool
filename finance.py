"""
Finance module for tracking API usage and estimated costs.

This module provides functions to calculate and report API costs
based on usage data stored in the project state database.
"""

import sqlite3
from typing import Dict, List


class FinanceTracker:
    """Handles financial tracking of API usage and costs."""

    def __init__(self, db_file="project_state.db"):
        self.db_file = db_file

    def get_total_costs(self) -> Dict[str, float]:
        """Get total estimated costs per API."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT api_name, SUM(cost_estimate)
            FROM api_usage
            GROUP BY api_name
        """)

        costs = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return costs

    def get_usage_summary(self) -> List[Dict]:
        """Get summary of API usage with costs."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT api_name, endpoint, SUM(tokens_used), SUM(cost_estimate), COUNT(*)
            FROM api_usage
            GROUP BY api_name, endpoint
        """)

        summary = []
        for row in cursor.fetchall():
            summary.append({
                "api_name": row[0],
                "endpoint": row[1],
                "total_tokens": row[2],
                "total_cost": row[3],
                "call_count": row[4]
            })

        conn.close()
        return summary

    def get_monthly_costs(self, year: int, month: int) -> Dict[str, float]:
        """Get costs for a specific month."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT api_name, SUM(cost_estimate)
            FROM api_usage
            WHERE strftime('%Y', timestamp) = ? AND strftime('%m', timestamp) = ?
            GROUP BY api_name
        """, (f"{year:04d}", f"{month:02d}"))

        costs = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return costs


def print_cost_report():
    """Print a cost report to console (for admin use)."""
    tracker = FinanceTracker()
    total_costs = tracker.get_total_costs()
    summary = tracker.get_usage_summary()

    print("=== API Cost Report ===")
    print(f"Total Costs: {total_costs}")
    print("\nUsage Summary:")
    for item in summary:
        print(f"- {item['api_name']} ({item['endpoint']}): {item['total_tokens']} tokens, ${item['total_cost']:.4f}, {item['call_count']} calls")


if __name__ == "__main__":
    print_cost_report()