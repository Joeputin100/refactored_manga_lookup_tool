#!/usr/bin/env python3
"""
Pre-seed process monitor
Checks pre-seed progress every 10 minutes and restarts if needed
"""
import time
import subprocess
import os
import sys
from datetime import datetime

class PreSeedMonitor:
    def __init__(self):
        self.log_file = "pre_seed_complete.log"
        self.script_path = "pre_seed_cache_fixed.py"
        self.check_interval = 600  # 10 minutes
        self.max_restarts = 3
        self.restart_count = 0

    def check_process_running(self):
        """Check if pre-seed process is running"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", self.script_path],
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except Exception as e:
            print(f"❌ Error checking process: {e}")
            return False

    def get_progress(self):
        """Get current progress from log file"""
        if not os.path.exists(self.log_file):
            return {
                'status': 'not_started',
                'progress': 0,
                'success': 0,
                'failed': 0,
                'elapsed': 'unknown'
            }

        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()

            # Get last progress line
            progress_lines = [line for line in lines if "Progress:" in line]
            if not progress_lines:
                return {
                    'status': 'no_progress',
                    'progress': 0,
                    'success': 0,
                    'failed': 0,
                    'elapsed': 'unknown'
                }

            last_progress = progress_lines[-1]

            # Extract progress info
            progress_parts = last_progress.split("|")
            progress_info = {}

            for part in progress_parts:
                if "Progress:" in part:
                    progress_info['progress'] = part.split("Progress:")[1].strip()
                elif "Success:" in part:
                    progress_info['success'] = int(part.split("Success:")[1].strip())
                elif "Failed:" in part:
                    progress_info['failed'] = int(part.split("Failed:")[1].strip())
                elif "Elapsed:" in part:
                    progress_info['elapsed'] = part.split("Elapsed:")[1].strip()

            return {
                'status': 'running',
                'progress': progress_info.get('progress', '0/55'),
                'success': progress_info.get('success', 0),
                'failed': progress_info.get('failed', 0),
                'elapsed': progress_info.get('elapsed', 'unknown')
            }

        except Exception as e:
            print(f"❌ Error reading progress: {e}")
            return {
                'status': 'error',
                'progress': 'error',
                'success': 0,
                'failed': 0,
                'elapsed': 'error'
            }

    def restart_process(self):
        """Restart the pre-seed process"""
        if self.restart_count >= self.max_restarts:
            print(f"❌ Max restarts reached ({self.max_restarts}). Giving up.")
            return False

        print(f"🔄 Restarting pre-seed process (attempt {self.restart_count + 1}/{self.max_restarts})...")

        try:
            # Kill any existing process
            subprocess.run(["pkill", "-f", self.script_path], capture_output=True)

            # Start new process
            with open(self.log_file, 'a') as f:
                f.write(f"\n=== RESTARTED AT {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

            subprocess.Popen(
                ["nohup", "python3", self.script_path, ">>", self.log_file, "2>&1", "&"],
                shell=True
            )

            self.restart_count += 1
            print("✅ Pre-seed process restarted")
            return True

        except Exception as e:
            print(f"❌ Failed to restart process: {e}")
            return False

    def check_and_restart_if_needed(self):
        """Check if process needs restart and restart if needed"""
        is_running = self.check_process_running()
        progress = self.get_progress()

        print(f"\n🕐 Check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Status: {'Running' if is_running else 'Not Running'}")
        print(f"📈 Progress: {progress['progress']}")
        print(f"✅ Success: {progress['success']}")
        print(f"❌ Failed: {progress['failed']}")
        print(f"⏱️  Elapsed: {progress['elapsed']}")

        # Check if process needs restart
        needs_restart = False

        if not is_running:
            print("⚠️  Process not running - needs restart")
            needs_restart = True
        elif progress['status'] == 'error':
            print("⚠️  Progress reading error - needs restart")
            needs_restart = True
        elif progress['status'] == 'no_progress':
            print("⚠️  No progress detected - needs restart")
            needs_restart = True

        if needs_restart:
            return self.restart_process()
        else:
            print("✅ Process running normally")
            return True

    def run_monitor(self):
        """Run the monitoring loop"""
        print("🎯 Pre-Seed Process Monitor Started")
        print("=" * 60)
        print(f"📊 Monitoring: {self.script_path}")
        print(f"⏰ Check interval: {self.check_interval} seconds")
        print(f"🔄 Max restarts: {self.max_restarts}")
        print("=" * 60)

        while True:
            try:
                success = self.check_and_restart_if_needed()

                if not success:
                    print("❌ Monitor stopping due to restart failure")
                    break

                print(f"⏰ Next check in {self.check_interval} seconds...")
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                print("\n🛑 Monitor stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(60)  # Wait 1 minute before retry

if __name__ == "__main__":
    monitor = PreSeedMonitor()
    monitor.run_monitor()