# EC2 SSH Connection Troubleshooting

## Using EC2 Instance Connect

### Method 1: AWS Management Console
1. Go to AWS Management Console → EC2
2. Navigate to "Instances"
3. Select your EC2 instance
4. Click "Connect" button
5. Choose "EC2 Instance Connect" tab
6. Click "Connect" - this opens a browser-based terminal

### Method 2: AWS CLI with EC2 Instance Connect
```bash
# Install AWS CLI if not already installed
pip install awscli

# Configure AWS credentials
aws configure

# Connect using EC2 Instance Connect
aws ec2-instance-connect ssh \
    --instance-id i-YOUR_INSTANCE_ID \
    --region us-east-2
```

## SSH Connection Troubleshooting

### Common Issues and Solutions

#### 1. Security Group Issues
- **Problem**: Port 22 blocked
- **Solution**:
  - Check Security Group inbound rules
  - Ensure port 22 is open for your IP (or 0.0.0.0/0 for testing)
  - Rules should allow: SSH (port 22) from your IP

#### 2. Instance State
- **Problem**: Instance not running
- **Solution**:
  - Check instance state in AWS Console
  - Start instance if stopped
  - Wait for "running" status

#### 3. Key Pair Issues
- **Problem**: Wrong key pair or permissions
- **Solution**:
  - Verify correct key pair is associated with instance
  - Ensure private key file has correct permissions:
    ```bash
    chmod 400 your-key.pem
    ```

#### 4. Network ACL Issues
- **Problem**: Network ACL blocking traffic
- **Solution**:
  - Check VPC Network ACLs
  - Ensure inbound/outbound rules allow SSH

#### 5. Instance Connectivity
- **Problem**: Instance not reachable
- **Solution**:
  - Check if instance has public IP
  - Verify internet gateway is attached to VPC
  - Check route tables

## Step-by-Step Connection Test

### Step 1: Verify Instance Status
```bash
# Using AWS CLI
aws ec2 describe-instances --instance-ids i-YOUR_INSTANCE_ID

# Look for:
# - "State": "running"
# - "PublicIpAddress": should have a value
# - "KeyName": should match your key pair
```

### Step 2: Check Security Groups
```bash
# Get security group ID
aws ec2 describe-instances --instance-ids i-YOUR_INSTANCE_ID --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId'

# Check security group rules
aws ec2 describe-security-groups --group-ids sg-YOUR_SECURITY_GROUP_ID
```

### Step 3: Test Basic Connectivity
```bash
# Test if instance is reachable
ping YOUR_INSTANCE_PUBLIC_IP

# Test port 22
telnet YOUR_INSTANCE_PUBLIC_IP 22

# If ping/telnet fail, there's a network issue
```

### Step 4: Manual SSH Connection
```bash
# Using key pair
ssh -i "your-key.pem" ec2-user@YOUR_INSTANCE_PUBLIC_IP

# If this fails, check:
# - Key file permissions (chmod 400)
# - Correct username (ec2-user for Amazon Linux)
# - Correct public IP
```

## Alternative Connection Methods

### 1. Session Manager (SSM)
If SSH is completely blocked, use AWS Systems Manager Session Manager:
```bash
# Install Session Manager plugin
# Then connect without SSH
aws ssm start-session --target i-YOUR_INSTANCE_ID
```

### 2. Bastion Host
If instance is in private subnet:
- Set up a bastion host in public subnet
- SSH to bastion, then to private instance

### 3. Direct Console Access
- Use EC2 Instance Connect via AWS Console
- No SSH configuration needed

## Quick Test Commands

Once connected via EC2 Instance Connect, run these commands:

```bash
# Test basic connectivity
echo "Connected to EC2 instance"

# Check current directory
pwd

# List files
ls -la

# Check if in the right directory
cd /home/ec2-user/refactored_manga_lookup_tool
ls -la

# Update code
git pull

# Test Vertex AI
python -c "import vertexai; print('Vertex AI available')"

# Run Streamlit
streamlit run app_new_workflow.py
```

## Common Error Messages and Solutions

- **"Connection timed out"**: Security group or network issue
- **"Permission denied (publickey)"**: Key pair issue
- **"Network is unreachable"**: Instance not running or no public IP
- **"Host key verification failed"**: Remove old host key from known_hosts

## Next Steps After Connection

1. **Update code**: `git pull`
2. **Test Vertex AI**: `python -c "import vertexai"`
3. **Run Streamlit**: `streamlit run app_new_workflow.py`
4. **Test with "Attack on Titan"**
5. **Verify all APIs work**

Let me know which connection method works for you and I can help with the next steps!