#!/usr/bin/env python3
"""
AWS Connection Monitor
Monitors AWS EC2 connectivity and retries every 15 minutes until stable
"""
import subprocess
import time
import sys
import os
from datetime import datetime

def test_aws_connection():
    """Test AWS EC2 connection"""
    try:
        # Test SSH connection
        result = subprocess.run([
            'ssh', '-i', '~/projects/Rosie/my-new-key.pem',
            'ec2-user@ec2-52-15-93-20.us-east-2.compute.amazonaws.com',
            'echo "Connection test successful"'
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print(f"✅ {datetime.now().strftime('%H:%M:%S')} - AWS connection successful")
            return True
        else:
            print(f"❌ {datetime.now().strftime('%H:%M:%S')} - AWS connection failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - AWS connection timeout")
        return False
    except Exception as e:
        print(f"❌ {datetime.now().strftime('%H:%M:%S')} - AWS connection error: {e}")
        return False

def run_mle_star_test():
    """Run MLE Star performance test when connection is stable"""
    print(f"🚀 {datetime.now().strftime('%H:%M:%S')} - Running MLE Star performance test...")

    try:
        # Copy test files to EC2
        files_to_copy = [
            'mle_star_cache_optimizer.py',
            'bulk_volume_test_mle_star.py',
            'test_mle_star_quick.py'
        ]

        for file in files_to_copy:
            subprocess.run([
                'scp', '-i', '~/projects/Rosie/my-new-key.pem',
                file,
                'ec2-user@ec2-52-15-93-20.us-east-2.compute.amazonaws.com:/home/ec2-user/refactored_manga_lookup_tool/'
            ], check=True)

        print(f"✅ {datetime.now().strftime('%H:%M:%S')} - Files copied to EC2")

        # Run quick MLE Star test
        result = subprocess.run([
            'ssh', '-i', '~/projects/Rosie/my-new-key.pem',
            'ec2-user@ec2-52-15-93-20.us-east-2.compute.amazonaws.com',
            'cd /home/ec2-user/refactored_manga_lookup_tool && python3 test_mle_star_quick.py'
        ], capture_output=True, text=True, timeout=300)

        print(f"📊 {datetime.now().strftime('%H:%M:%S')} - MLE Star test output:")
        print(result.stdout)
        if result.stderr:
            print(f"⚠️  Errors: {result.stderr}")

        return True

    except Exception as e:
        print(f"❌ {datetime.now().strftime('%H:%M:%S')} - MLE Star test failed: {e}")
        return False

def check_volume_background_job():
    """Check volume background job progress"""
    try:
        result = subprocess.run([
            'ssh', '-i', '~/projects/Rosie/my-new-key.pem',
            'ec2-user@ec2-52-15-93-20.us-east-2.compute.amazonaws.com',
            'cd /home/ec2-user/refactored_manga_lookup_tool && grep -c "✅ Loaded" volume_loading.log'
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            volume_count = result.stdout.strip()
            print(f"📚 {datetime.now().strftime('%H:%M:%S')} - Volume background job: {volume_count} volumes loaded")
            return volume_count
        else:
            print(f"❌ {datetime.now().strftime('%H:%M:%S')} - Failed to check volume job: {result.stderr}")
            return None

    except Exception as e:
        print(f"❌ {datetime.now().strftime('%H:%M:%S')} - Volume job check failed: {e}")
        return None

def main():
    """Main monitoring loop"""
    print("🔍 AWS Connection Monitor Started")
    print("📡 Monitoring EC2 instance every 15 minutes")
    print("⏰ Next check in 15 minutes...")

    connection_restored = False
    test_run = False

    while True:
        # Wait 15 minutes between checks
        time.sleep(900)  # 15 minutes in seconds

        print(f"\n🔄 {datetime.now().strftime('%H:%M:%S')} - Checking AWS connection...")

        # Test connection
        if test_aws_connection():
            if not connection_restored:
                print(f"🎉 {datetime.now().strftime('%H:%M:%S')} - AWS CONNECTION RESTORED!")
                connection_restored = True

                # Check volume background job
                volume_count = check_volume_background_job()

                # Run MLE Star test if not already run
                if not test_run:
                    print(f"🚀 {datetime.now().strftime('%H:%M:%S')} - Running MLE Star performance test...")
                    test_run = run_mle_star_test()

                    if test_run:
                        print(f"✅ {datetime.now().strftime('%H:%M:%S')} - MLE Star test completed successfully")
                    else:
                        print(f"❌ {datetime.now().strftime('%H:%M:%S')} - MLE Star test failed")
            else:
                print(f"✅ {datetime.now().strftime('%H:%M:%S')} - Connection still stable")

                # Check volume job progress periodically
                if int(datetime.now().strftime('%M')) % 30 == 0:  # Every 30 minutes
                    volume_count = check_volume_background_job()
        else:
            connection_restored = False
            test_run = False
            print(f"❌ {datetime.now().strftime('%H:%M:%S')} - Connection still unstable")
            print("⏰ Next check in 15 minutes...")

if __name__ == "__main__":
    main()