#!/usr/bin/env python3
"""
Context state JSON saving system
Saves state with each interaction for debugging and optimization
"""
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional
import subprocess
import hashlib

class ContextStateSaver:
    """Saves context state with each interaction"""

    def __init__(self, save_dir: str = "context_states"):
        self.save_dir = save_dir
        self.current_state = {}
        self.ensure_save_dir()

    def ensure_save_dir(self):
        """Ensure the save directory exists"""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            print(f"✅ Created context state directory: {self.save_dir}")

    def get_git_info(self) -> Dict[str, str]:
        """Get current git commit and status"""
        git_info = {}

        try:
            # Get current commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            if result.returncode == 0:
                git_info['commit'] = result.stdout.strip()[:8]

            # Get git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            if result.returncode == 0:
                git_info['status'] = result.stdout.strip()

        except Exception as e:
            git_info['error'] = str(e)

        return git_info

    def get_file_changes(self) -> Dict[str, Any]:
        """Get information about modified files"""
        file_changes = {}

        try:
            # Get list of modified files
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            if result.returncode == 0:
                modified_files = result.stdout.strip().split('\n')
                if modified_files and modified_files[0]:
                    file_changes['modified'] = modified_files

            # Get list of untracked files
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            if result.returncode == 0:
                untracked_files = result.stdout.strip().split('\n')
                if untracked_files and untracked_files[0]:
                    file_changes['untracked'] = untracked_files

        except Exception as e:
            file_changes['error'] = str(e)

        return file_changes

    def generate_filename(self, summary: str) -> str:
        """Generate filename with timestamp and summary"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create a sanitized summary for filename
        sanitized_summary = "".join(
            c for c in summary.lower()
            if c.isalnum() or c in (' ', '-', '_')
        ).replace(' ', '_')[:50]

        return f"{timestamp}_{sanitized_summary}.json"

    def save_state(self,
                   state_data: Dict[str, Any],
                   summary: str,
                   interaction_type: str = "general") -> str:
        """
        Save context state to JSON file

        Args:
            state_data: The state data to save
            summary: One-sentence summary of current state
            interaction_type: Type of interaction (e.g., "cache_test", "api_call", "optimization")

        Returns:
            Path to saved file
        """
        # Build complete state
        complete_state = {
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'interaction_type': interaction_type,
            'git_info': self.get_git_info(),
            'file_changes': self.get_file_changes(),
            'state_data': state_data,
            'metadata': {
                'python_version': os.sys.version,
                'working_directory': os.getcwd(),
                'script_path': os.path.abspath(__file__)
            }
        }

        # Generate filename
        filename = self.generate_filename(summary)
        filepath = os.path.join(self.save_dir, filename)

        # Save to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(complete_state, f, indent=2, ensure_ascii=False, default=str)

            print(f"💾 Saved context state: {filename}")
            print(f"   Summary: {summary}")
            print(f"   Type: {interaction_type}")

            return filepath

        except Exception as e:
            print(f"❌ Failed to save context state: {e}")
            return ""

    def save_cache_test_state(self,
                             test_results: Dict[str, Any],
                             series_list: list,
                             cache_hits: int,
                             cache_misses: int) -> str:
        """Save cache test state"""
        state_data = {
            'test_type': 'cache_performance',
            'series_tested': series_list,
            'cache_hits': cache_hits,
            'cache_misses': cache_misses,
            'hit_rate': cache_hits / len(series_list) if series_list else 0,
            'test_results': test_results,
            'total_series': len(series_list)
        }

        summary = f"Cache test with {cache_hits} hits and {cache_misses} misses"
        return self.save_state(state_data, summary, "cache_test")

    def save_api_optimization_state(self,
                                   optimization_stats: Dict[str, Any],
                                   series_count: int,
                                   speedup: float) -> str:
        """Save API optimization state"""
        state_data = {
            'optimization_type': 'api_batching',
            'series_count': series_count,
            'speedup_factor': speedup,
            'optimization_stats': optimization_stats
        }

        summary = f"API optimization with {speedup:.2f}x speedup for {series_count} series"
        return self.save_state(state_data, summary, "api_optimization")

    def save_warning_state(self,
                          warning_count: int,
                          warning_types: list,
                          suppression_status: str) -> str:
        """Save warning suppression state"""
        state_data = {
            'warning_count': warning_count,
            'warning_types': warning_types,
            'suppression_status': suppression_status,
            'suppression_methods': ['vertex_ai', 'streamlit', 'alts_creds']
        }

        summary = f"Warning suppression for {warning_count} warnings"
        return self.save_state(state_data, summary, "warning_suppression")

    def list_saved_states(self) -> list:
        """List all saved context states"""
        try:
            files = os.listdir(self.save_dir)
            json_files = [f for f in files if f.endswith('.json')]
            return sorted(json_files)
        except Exception as e:
            print(f"❌ Failed to list saved states: {e}")
            return []

def test_context_state_saver():
    """Test the context state saver"""
    print("🔍 Testing Context State Saver")
    print("=" * 50)

    saver = ContextStateSaver()

    # Test basic state saving
    test_state = {
        'test_value': 'hello world',
        'numbers': [1, 2, 3, 4, 5],
        'nested': {
            'key': 'value',
            'list': ['a', 'b', 'c']
        }
    }

    # Save basic state
    filepath = saver.save_state(
        test_state,
        "Basic context state test with nested data",
        "test"
    )

    if filepath:
        print(f"✅ Basic state saved to: {filepath}")

    # Test cache test state
    cache_results = {
        'cache_hits': 8,
        'cache_misses': 2,
        'response_times': [0.1, 0.2, 0.15, 0.12, 0.18],
        'average_time': 0.15
    }

    cache_filepath = saver.save_cache_test_state(
        cache_results,
        ['Attack on Titan', 'One Piece', 'Naruto', 'Dragon Ball Z', 'Berserk'],
        8, 2
    )

    # List saved states
    saved_states = saver.list_saved_states()
    print(f"\n📁 Saved states: {len(saved_states)}")
    for state_file in saved_states[:5]:  # Show first 5
        print(f"   📄 {state_file}")

    print("\n✅ Context state saver test completed")

if __name__ == "__main__":
    test_context_state_saver()