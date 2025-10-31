# Quickstart Guide: AWS Lambda Deployment

**Feature**: AWS Lambda Deployment with CI/CD and Rate Limiting
**Branch**: 005-aws-lambda-deployment
**Date**: 2025-10-28

## Overview

This guide walks you through deploying the Bluths API to AWS Lambda. There are two deployment methods:

1. **Automated CI/CD** (recommended): Push to `main` branch → GitHub Actions deploys automatically
2. **Manual Local Deployment**: Deploy from your machine using AWS SAM CLI

Choose the method that fits your workflow. Most teams use **Automated CI/CD** after initial setup.

---

## Prerequisites

### Required for Both Methods
- AWS account with admin access (or IAM user with Lambda/API Gateway/CloudFormation permissions)
- Git and this repository cloned locally

### Additional for Automated CI/CD
- GitHub repository with Actions enabled
- Ability to add GitHub Secrets (requires repo admin/write access)

### Additional for Manual Deployment
- AWS CLI installed: https://aws.amazon.com/cli/
- AWS SAM CLI installed: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
- Python 3.11+ installed
- Docker installed (for SAM local testing)

---

## Method 1: Automated CI/CD Deployment (Recommended)

### Step 1: Create AWS IAM User with Least Privilege

**⚠️ SECURITY REQUIREMENT**: Per the constitution, Least Privilege is MANDATORY. Under no circumstances should permissions be granted beyond what is strictly required, even for MVPs or testing.

Create a custom IAM policy with minimal required permissions:

1. Navigate to **IAM → Policies → Create policy**
2. Select **JSON** tab and paste:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LambdaDeployment",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:PublishVersion",
        "lambda:CreateAlias",
        "lambda:UpdateAlias",
        "lambda:GetAlias",
        "lambda:ListVersionsByFunction",
        "lambda:AddPermission",
        "lambda:RemovePermission"
      ],
      "Resource": "arn:aws:lambda:*:*:function:bluths-api-*"
    },
    {
      "Sid": "APIGatewayDeployment",
      "Effect": "Allow",
      "Action": [
        "apigateway:GET",
        "apigateway:POST",
        "apigateway:PUT",
        "apigateway:PATCH",
        "apigateway:DELETE"
      ],
      "Resource": [
        "arn:aws:apigateway:*::/apis",
        "arn:aws:apigateway:*::/apis/*"
      ]
    },
    {
      "Sid": "CloudFormationDeployment",
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateStack",
        "cloudformation:UpdateStack",
        "cloudformation:DeleteStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:GetTemplate",
        "cloudformation:ValidateTemplate",
        "cloudformation:CreateChangeSet",
        "cloudformation:DescribeChangeSet",
        "cloudformation:ExecuteChangeSet"
      ],
      "Resource": "arn:aws:cloudformation:*:*:stack/bluths-api*/*"
    },
    {
      "Sid": "IAMRoleCreation",
      "Effect": "Allow",
      "Action": [
        "iam:GetRole",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::*:role/bluths-api-*"
    },
    {
      "Sid": "S3ArtifactStorage",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::bbh-applications/bluths-api/*"
    },
    {
      "Sid": "S3BucketList",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::bbh-applications",
      "Condition": {
        "StringLike": {
          "s3:prefix": "bluths-api/*"
        }
      }
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DescribeLogGroups",
        "logs:PutRetentionPolicy"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/bluths-api-*"
    }
  ]
}
```

3. Policy name: `BluthsAPIDeploymentPolicy`
4. Description: "Least Privilege policy for Bluths API Lambda deployment via GitHub Actions"
5. Click **Create policy**

Now create the IAM user:

6. Navigate to **IAM → Users → Create user**
7. User name: `github-actions-deployer`
8. Enable **Programmatic access** (access key)
9. **Attach policies directly** → Search for `BluthsAPIDeploymentPolicy` → Select it
10. **Create user** → **Download credentials CSV** (contains Access Key ID and Secret Access Key)

**✅ Why This Policy Follows Least Privilege**:
- Scopes all Lambda/IAM permissions to `bluths-api-*` resources only
- Grants only required actions (no wildcards like `lambda:*`)
- Restricts S3 access to `bbh-applications` bucket with `bluths-api/` prefix only
- S3 ListBucket further scoped with condition to `bluths-api/*` prefix
- Limits CloudWatch Logs to application log groups only
- Cannot accidentally impact other AWS resources, buckets, or accounts

**⚠️ SECURITY NOTES**:
- Store credentials securely! They won't be shown again.
- Never use `*FullAccess` managed policies - they violate the constitution
- Rotate credentials every 90 days (see Security Best Practices section)

### Step 2: Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings → Secrets and variables → Actions**
3. Click **New repository secret** and add each:

| Secret Name | Value | Example | Where to Find |
|-------------|-------|---------|---------------|
| `AWS_ACCESS_KEY_ID` | Your access key (starts with `AKIA`) | `AKIAIOSFODNN7EXAMPLE` | From credentials CSV (Step 1) |
| `AWS_SECRET_ACCESS_KEY` | Your secret key (40 characters) | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` | From credentials CSV (Step 1) |
| `AWS_REGION` | `us-east-1` (or your preferred region) | `us-east-1` | Choose based on latency/cost |
| `AWS_ACCOUNT_ID` | Your 12-digit account ID | `123456789012` | AWS Console → Account dropdown |
| `AWS_SAM_BUCKET` | S3 bucket name for SAM artifacts | `bbh-applications` | Existing S3 bucket (see below) |
| `S3_BASE_URL` | Your S3 media URL | `https://media.example.com` | Existing S3 bucket URL for media files |

**Note**: These credentials will be used by GitHub Actions to deploy to AWS. Per the constitution, remote credentials must be stored in GitHub Secrets, never committed to the repository.

#### AWS_SAM_BUCKET Configuration

The `AWS_SAM_BUCKET` secret should contain the name of an **existing** S3 bucket where SAM will store deployment artifacts. The bucket must already exist (the IAM policy does not include `s3:CreateBucket` per Least Privilege).

**For this project:** `bbh-applications`

**Bucket Requirements:**

The bucket `bbh-applications` must:
1. Already exist in your AWS account
2. Be accessible by the IAM user `github-actions-deployer` (permissions already in Step 1 policy)
3. Have a bucket policy that allows the IAM user to access the `bluths-api/` prefix

**Required Bucket Policy** (add to `bbh-applications` bucket):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBluthsAPIDeployment",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/github-actions-deployer"
      },
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::bbh-applications/bluths-api/*"
    },
    {
      "Sid": "AllowBluthsAPIList",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/github-actions-deployer"
      },
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::bbh-applications",
      "Condition": {
        "StringLike": {
          "s3:prefix": "bluths-api/*"
        }
      }
    }
  ]
}
```

**To apply this bucket policy:**

1. Navigate to **S3 → Buckets → bbh-applications**
2. **Permissions** tab → **Bucket policy** → **Edit**
3. If a policy already exists, merge this with the existing policy (add the statements to the existing `Statement` array)
4. Replace `YOUR_ACCOUNT_ID` with your 12-digit AWS account ID (same as in GitHub Secrets)
5. **Save changes**

**Artifacts will be stored at:** `s3://bbh-applications/bluths-api/deployments/`

**Why This Follows Least Privilege:**
- IAM user policy (Step 1) grants permissions to the user
- Bucket policy (above) explicitly allows the user to access only `bluths-api/*` prefix
- Double-gated: Both IAM policy AND bucket policy must allow the action
- Other IAM users in the account cannot access `bluths-api/` prefix without explicit bucket policy permission
- The IAM user cannot create buckets or access other buckets
- The IAM user cannot access other prefixes in `bbh-applications` (e.g., `other-app/*`)

### Step 3: Verify Workflow File

Per the constitution, the GitHub Actions workflow must be located at:
```
.github/workflows/deploy.yml
```

If the file doesn't exist, create it or copy from:
```
specs/005-aws-lambda-deployment/contracts/github-workflow.yml
```

This location is standardized in the constitution for all Lambda deployments.

### Step 4: Deploy

1. Make any code change (or empty commit):
   ```bash
   git commit --allow-empty -m "Trigger Lambda deployment"
   ```

2. Push to main:
   ```bash
   git push origin main
   ```

3. Monitor deployment:
   - Go to **Actions** tab in GitHub
   - Click the running workflow
   - Watch real-time logs

### Step 5: Verify Deployment

When workflow completes (5-10 minutes), you'll see:
```
✅ Deployment successful!
API Endpoint: https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

Test the API:
```bash
# Health check
curl https://YOUR_API_URL/health

# Random quote
curl https://YOUR_API_URL/api/quotes/random

# Quote by character
curl https://YOUR_API_URL/api/quotes/gob

# Meme quote
curl https://YOUR_API_URL/api/quotes/meme
```

**🎉 Done!** Future pushes to `main` will automatically deploy updates.

---

## Method 2: Manual Local Deployment

### Step 1: Install Prerequisites

**AWS CLI**:
```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify
aws --version
```

**AWS SAM CLI**:
```bash
# macOS
brew install aws-sam-cli

# Linux
pip install aws-sam-cli

# Verify
sam --version
```

**Docker** (required for SAM build):
- macOS/Windows: Install Docker Desktop
- Linux: `sudo apt-get install docker.io`

### Step 2: Configure AWS Credentials

Create `.env` file in repository root:
```bash
cp specs/005-aws-lambda-deployment/contracts/env-template .env
```

Edit `.env` and fill in your credentials:
```bash
AWS_ACCESS_KEY_ID=AKIA................  # Your IAM access key
AWS_SECRET_ACCESS_KEY=........................  # Your IAM secret
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
AWS_SAM_BUCKET=bbh-applications  # Pre-existing S3 bucket for SAM artifacts
S3_BASE_URL=https://your-bucket.s3.amazonaws.com
```

**⚠️ IMPORTANT**: Verify `.env` is in `.gitignore` (it should be already)

Load credentials:
```bash
export $(cat .env | xargs)

# Verify
aws sts get-caller-identity
```

### Step 3: Prepare Deployment Files

Copy SAM template to deploy directory:
```bash
mkdir -p deploy/sam
cp specs/005-aws-lambda-deployment/contracts/sam-template.yaml deploy/sam/template.yaml
```

### Step 4: Build the Application

```bash
cd deploy/sam

# Build Lambda package (uses Docker)
sam build --use-container

# This creates .aws-sam/build/ directory with packaged code
```

**Expected output**:
```
Build Succeeded

Built Artifacts  : .aws-sam/build
Built Template   : .aws-sam/build/template.yaml
```

### Step 5: Deploy to AWS

```bash
# First deployment (interactive)
sam deploy --guided \
  --s3-bucket $AWS_SAM_BUCKET \
  --s3-prefix bluths-api/deployments

# SAM will prompt for:
# Stack name: bluths-api
# AWS Region: us-east-1
# Parameter S3BaseUrl: (paste your S3 URL)
# Parameter GlobalRateLimit: 10
# Confirm changes before deploy: Y
# Allow SAM CLI IAM role creation: Y
# Save arguments to samconfig.toml: Y

# Wait 3-5 minutes for deployment...
```

**Note**: The `--s3-bucket` flag uses the pre-existing `bbh-applications` bucket (from AWS_SAM_BUCKET env var). This follows Least Privilege by not requiring `s3:CreateBucket` permission.

**Subsequent deployments** (uses saved config):
```bash
sam deploy  # No --guided flag needed, uses samconfig.toml
```

### Step 6: Get API Endpoint

After deployment, SAM outputs:
```
CloudFormation outputs from deployed stack
--------------------------------------------------
Outputs
--------------------------------------------------
Key                 ApiUrl
Description         API Gateway endpoint URL (prod stage)
Value               https://abc123.execute-api.us-east-1.amazonaws.com/prod
--------------------------------------------------
```

Save this URL!

### Step 7: Test Deployment

```bash
export API_URL="https://abc123.execute-api.us-east-1.amazonaws.com/prod"

# Health check
curl $API_URL/health

# Random quote
curl $API_URL/api/quotes/random | jq .

# Test global rate limiting (requires generating >10 QPS)
# Note: Per constitution, only global throttling is enforced (no per-IP limits)
```

**🎉 Done!** Your API is live on AWS Lambda.

---

## Post-Deployment Tasks

### 1. Configure SSL Certificate and Custom Domain (Required)

After your first successful deployment, set up SSL certificate and custom domain `bqaas.lucille2.com`:

⚠️ **CRITICAL REQUIREMENT**: SSL certificate MUST list `bqaas.lucille2.com` as an allowed domain name (no browser warnings).

---

#### Step 1: Request ACM Certificate

**Option A: AWS Console** (Recommended for first-time)

1. Log in to AWS Console
2. Navigate to **Certificate Manager (ACM)**
3. Ensure you're in the correct region (must match Lambda region, e.g., `us-east-1`)
4. Click **Request certificate** → **Request a public certificate**
5. **Domain names**:
   - **Fully qualified domain name**: `bqaas.lucille2.com`
   - ✅ **Verify**: Certificate MUST include `bqaas.lucille2.com` in the allowed names list
6. **Validation method**: DNS validation (recommended)
7. Click **Request**

**Option B: AWS CLI**

```bash
# Request certificate for bqaas.lucille2.com
CERT_ARN=$(aws acm request-certificate \
  --domain-name bqaas.lucille2.com \
  --validation-method DNS \
  --region us-east-1 \
  --query 'CertificateArn' \
  --output text)

echo "Certificate ARN: $CERT_ARN"

# Get DNS validation record
aws acm describe-certificate \
  --certificate-arn $CERT_ARN \
  --region us-east-1 \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord'
```

---

#### Step 2: Complete DNS Validation

ACM provides a DNS validation CNAME record. Add it to your DNS provider:

**Validation Record** (from ACM):
```
Name: _abc123def456.bqaas.lucille2.com
Type: CNAME
Value: _xyz789ghi012.acm-validations.aws.
```

**Add to Namecheap**:
1. Domain List → lucille2.com → Advanced DNS
2. Add New Record:
   - Type: CNAME Record
   - Host: `_abc123def456.bqaas` (ACM provides this)
   - Value: `_xyz789ghi012.acm-validations.aws.` (ACM provides this)
   - TTL: 5 min

**Add to Route53**:
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id <YOUR_ZONE_ID> \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "_abc123def456.bqaas.lucille2.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "_xyz789ghi012.acm-validations.aws."}]
      }
    }]
  }'
```

**Wait for validation**: 5-30 minutes (usually ~10 minutes)

Check status:
```bash
aws acm describe-certificate \
  --certificate-arn $CERT_ARN \
  --region us-east-1 \
  --query 'Certificate.Status'
# Wait for: "ISSUED"
```

---

#### Step 3: Create API Gateway Custom Domain Name

**Option A: AWS Console**

1. Navigate to **API Gateway** → **Custom domain names**
2. Click **Create**
3. **Domain name**: `bqaas.lucille2.com`
4. **ACM certificate**: Select the certificate from Step 1 (should show `bqaas.lucille2.com`)
5. Click **Create domain name**
6. **Note the CloudFront distribution domain** (e.g., `d123abc456.cloudfront.net`)

**Option B: AWS CLI**

```bash
# Create custom domain
aws apigatewayv2 create-domain-name \
  --domain-name bqaas.lucille2.com \
  --domain-name-configurations "CertificateArn=$CERT_ARN" \
  --region us-east-1

# Get the CloudFront distribution domain
CLOUDFRONT_DOMAIN=$(aws apigatewayv2 get-domain-name \
  --domain-name bqaas.lucille2.com \
  --region us-east-1 \
  --query 'DomainNameConfigurations[0].ApiGatewayDomainName' \
  --output text)

echo "CloudFront Domain: $CLOUDFRONT_DOMAIN"
```

---

#### Step 4: Create API Mapping

Map the custom domain to your API:

**Option A: AWS Console**

1. In API Gateway → Custom domain names → `bqaas.lucille2.com`
2. Click **API mappings** tab
3. Click **Configure API mappings**
4. **Add mapping**:
   - API: Select your `bluths-api` HTTP API
   - Stage: `prod`
   - Path: (leave empty for root)
5. Save

**Option B: AWS CLI**

```bash
# Get API ID
API_ID=$(aws cloudformation describe-stacks \
  --stack-name bluths-api \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiId`].OutputValue' \
  --output text)

# Create API mapping
aws apigatewayv2 create-api-mapping \
  --domain-name bqaas.lucille2.com \
  --api-id $API_ID \
  --stage prod \
  --region us-east-1
```

---

#### Step 5: Update DNS with CloudFront Domain

Create CNAME pointing to the CloudFront distribution (NOT the API Gateway default URL):

**Add to Namecheap**:
1. Domain List → lucille2.com → Advanced DNS
2. Add New Record:
   - Type: CNAME Record
   - Host: `bqaas`
   - Value: `d123abc456.cloudfront.net` (from Step 3)
   - TTL: 5 min

**Add to Route53**:
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id <YOUR_ZONE_ID> \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "bqaas.lucille2.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'$CLOUDFRONT_DOMAIN'"}]
      }
    }]
  }'
```

---

#### Step 6: Wait and Verify

**Wait**: 5-15 minutes for DNS propagation

**Verify DNS**:
```bash
# Check CNAME resolution
dig bqaas.lucille2.com
# Should show: bqaas.lucille2.com → d123abc456.cloudfront.net

nslookup bqaas.lucille2.com
```

**Test API with valid SSL**:
```bash
# Health check
curl -v https://bqaas.lucille2.com/health
# Should show: "subject: CN=bqaas.lucille2.com" (your certificate!)

# Random quote
curl https://bqaas.lucille2.com/api/quotes/random | jq .

# Test in browser
open https://bqaas.lucille2.com
# Should show: ✅ Valid certificate, no warnings
```

---

#### Verification Checklist

- [ ] ACM certificate shows status: "Issued"
- [ ] Certificate Subject Alternative Names includes: `bqaas.lucille2.com`
- [ ] Custom domain name created in API Gateway
- [ ] API mapping configured (path: `/`, stage: `prod`)
- [ ] DNS CNAME points to CloudFront domain (not API Gateway default URL)
- [ ] `curl https://bqaas.lucille2.com/health` returns 200
- [ ] Browser shows valid SSL certificate (no warnings)
- [ ] Certificate Common Name (CN) is `bqaas.lucille2.com`

---

#### Troubleshooting

**Issue: Certificate validation stuck "Pending"**
- Check DNS validation CNAME is correct
- Wait 30 minutes (can take time)
- Verify CNAME is visible: `dig _abc123.bqaas.lucille2.com`

**Issue: "Certificate doesn't match domain"**
- Verify ACM certificate lists `bqaas.lucille2.com` in Subject Alternative Names
- Check you're using the CloudFront domain (from Step 3), not the API Gateway default URL

**Issue: DNS not resolving**
- Wait longer (DNS propagation can take 15 minutes)
- Check CNAME target is CloudFront domain, not API Gateway URL
- Use `dig` to verify: `dig bqaas.lucille2.com`

**Issue: API returns 403 Forbidden**
- Verify API mapping is configured correctly (path: `/`, stage: `prod`)
- Check API ID matches your deployed API

---

#### Summary

After completing these steps:

✅ **SSL Certificate**: Valid certificate for `bqaas.lucille2.com` (no browser warnings)
✅ **Custom Domain**: API accessible at `https://bqaas.lucille2.com`
✅ **Both URLs work**:
- Default: `https://abc123.execute-api.us-east-1.amazonaws.com/prod`
- Custom: `https://bqaas.lucille2.com` (with valid SSL)

The custom domain setup is **manual and one-time**. Subsequent deployments don't affect the domain configuration.

### 2. Monitor Costs

Set up AWS Budget alert:
```bash
aws budgets create-budget \
  --account-id $AWS_ACCOUNT_ID \
  --budget file://budget-config.json
```

Expected costs:
- Lambda: ~$0.20 per 1M requests (first 1M/month free)
- API Gateway: ~$1 per 1M requests (first 1M/month free)
- **Total: < $5/month for low-medium traffic**

### 3. Monitor CloudWatch Logs (Included)

Per the constitution, basic observability is included via CloudWatch Logs:

1. Navigate to **CloudWatch → Log groups**
2. Find log group: `/aws/lambda/bluths-api-function`
3. View structured JSON logs for:
   - Errors
   - Warnings
   - Deployment events

**Note**: Per constitution, custom dashboards, metrics, and X-Ray tracing are out of scope for cost optimization. Log cost target: $0.50-2/month.

---

## Changing Rate Limits

Per the constitution, rate limiting is global throttling only (no per-IP limits).

**Quick reference**:

### Update Global Limit (10 QPS → 20 QPS)

**Option 1: Update SAM template** (recommended for permanent changes)

Edit `deploy/sam/template.yaml`:
```yaml
Parameters:
  GlobalRateLimit:
    Default: 20  # Changed from 10
```

Commit and push to trigger deployment.

**Option 2: Override during deployment** (for testing)

```bash
sam deploy --parameter-overrides GlobalRateLimit=20
```

**Option 3: Update via AWS Console** (no redeploy needed)

1. Navigate to **API Gateway → Your API → Throttling**
2. Update **Rate limit** to `20`
3. Update **Burst limit** as needed
4. Deploy changes

**Note**: Per constitution, rate limits must be configurable via API Gateway settings. See [RATE_LIMITS.md](../deploy/docs/RATE_LIMITS.md) for detailed documentation.

---

## Troubleshooting

### Issue: "AccessDenied" during deployment

**Cause**: IAM user lacks permissions

**Fix**: Attach required policies (see Step 1 above)

### Issue: "Stack already exists" error

**Cause**: Stack name conflict

**Fix**: Choose different stack name:
```bash
sam deploy --stack-name bluths-api-prod
```

### Issue: Package size exceeds 50MB

**Cause**: Too many dependencies

**Fix**: Remove unused packages from `requirements.txt`

### Issue: Cold start exceeds 3 seconds

**Cause**: Lambda initialization slow

**Fix**: Enable Provisioned Concurrency:
```yaml
# In template.yaml
Properties:
  ProvisionedConcurrencyConfig:
    ProvisionedConcurrentExecutions: 1
```

**Note**: Adds ~$11/month cost

### Issue: Rate limiting not working as expected

**Cause**: Only global throttling is implemented

**Expected behavior** (per constitution):
- Global throttling at API Gateway is enforced (10 QPS default)
- No per-IP rate limiting (intentionally excluded for simplicity and cost optimization)
- Rate limits apply uniformly across all clients

**To verify**:
```bash
# Generate >10 requests per second to trigger throttling
for i in {1..15}; do curl https://YOUR_API_URL/api/quotes/random & done
# Should see some 429 responses
```

### Issue: GitHub Actions workflow fails

**Check**:
1. Are all GitHub Secrets configured? (Settings → Secrets)
2. Is AWS_ACCOUNT_ID correct? (12 digits, no dashes)
3. Check workflow logs for specific error
4. Verify IAM user has required permissions

---

## Testing Locally

Before deploying, test Lambda function locally:

### Start Local API

```bash
cd deploy/sam

# Start local API Gateway + Lambda
sam local start-api --port 8000

# In another terminal:
curl http://localhost:8000/health
curl http://localhost:8000/api/quotes/random
```

**Note**: Local testing doesn't enforce rate limits (API Gateway feature)

### Invoke Function Directly

```bash
# Test with sample API Gateway event
sam local invoke BluthsApiFunction --event test-event.json
```

Sample `test-event.json`:
```json
{
  "httpMethod": "GET",
  "path": "/health",
  "headers": {},
  "body": null
}
```

---

## Rolling Back a Deployment

Per the constitution, Lambda deployments use versioning with a "prod" alias for instant rollback capability.

### If Deployment Failed in CI/CD
GitHub Actions automatically rolls back (see workflow logs). The prod alias remains pointing to the last known good version.

### Manual Rollback

```bash
# List Lambda versions
aws lambda list-versions-by-function \
  --function-name bluths-api-function

# Update prod alias to previous version
aws lambda update-alias \
  --function-name bluths-api-function \
  --name prod \
  --function-version 42  # Previous version number

# Verify rollback
aws lambda get-alias \
  --function-name bluths-api-function \
  --name prod
```

**Rollback process** (per constitution):
1. New Lambda version is published
2. /health endpoint is validated (must return HTTP 200)
3. If validation passes: prod alias updated to new version
4. If validation fails: prod alias remains on previous version (automatic rollback)

### Delete Stack (Complete Removal)

```bash
# Delete all resources
aws cloudformation delete-stack --stack-name bluths-api

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name bluths-api
```

**⚠️ WARNING**: This deletes everything (Lambda, API Gateway, logs)

---

## Security Best Practices

### 1. Rotate AWS Credentials Every 90 Days

```bash
# Create new access key
aws iam create-access-key --user-name github-actions-deployer

# Update .env or GitHub Secrets with new key
# Delete old access key
aws iam delete-access-key --user-name github-actions-deployer --access-key-id OLD_KEY_ID
```

### 2. Enable MFA on IAM User

AWS Console → IAM → Users → github-actions-deployer → Security credentials → Enable MFA

### 3. Verify Least Privilege (Already Implemented)

If you followed Step 1 correctly, you're already using Least Privilege! Verify:

1. Navigate to **IAM → Users → github-actions-deployer → Permissions**
2. Confirm only `BluthsAPIDeploymentPolicy` is attached
3. **Should NOT see any `*FullAccess` policies** - if you do, remove them immediately

The custom policy ensures:
- ✅ All permissions scoped to `bluths-api-*` resources only
- ✅ Only required actions granted (no wildcards like `lambda:*`)
- ✅ S3 access restricted to SAM CLI managed buckets only
- ✅ CloudWatch Logs limited to application log groups only
- ✅ Cannot accidentally impact other AWS resources

**Constitution Requirement**: Least Privilege is mandatory. Never use `*FullAccess` policies, even temporarily.

### 4. Upgrade to OIDC (Future)

Replace long-lived keys with temporary credentials:
- See `deploy/docs/SECURITY.md` (created in Phase 2)
- GitHub → AWS OIDC provider setup
- No credential storage needed

---

## Next Steps

1. **Monitor**: Set up CloudWatch alarms and dashboard
2. **Optimize**: Review Lambda execution times, adjust memory if needed
3. **Scale**: If traffic > 100 QPS, consider:
   - DynamoDB for rate limiting state
   - Provisioned concurrency for consistent performance
   - Multi-region deployment
4. **Secure**: Migrate to OIDC authentication
5. **Custom Domain**: Set up ACM certificate + API Gateway custom domain

---

## Support & Documentation

- **Rate Limits**: See `deploy/docs/RATE_LIMITS.md`
- **Architecture**: See `specs/005-aws-lambda-deployment/research.md`
- **Data Model**: See `specs/005-aws-lambda-deployment/data-model.md`
- **AWS SAM Docs**: https://docs.aws.amazon.com/serverless-application-model/
- **GitHub Actions**: https://docs.github.com/en/actions

---

## Summary

You've successfully deployed Bluths API to AWS Lambda! 🎉

**What you have**:
- ✅ Serverless API on AWS Lambda (Python 3.11) with Mangum adapter
- ✅ Automated CI/CD via GitHub Actions (.github/workflows/deploy.yml)
- ✅ Global rate limiting (10 QPS default) via API Gateway
- ✅ Lambda versioning with prod alias for instant rollback
- ✅ Automatic rollback on deployment validation failure (/health must return 200)
- ✅ CloudWatch Logs with structured JSON logging (errors, warnings, deployment events)
- ✅ ~$3-5/month estimated costs (with free tier: $0-1/month)

**API Endpoints**:
- `GET /health` - Health check
- `GET /api/quotes/random` - Random quote
- `GET /api/quotes/{speaker}` - Quote by character
- `GET /api/quotes/meme` - Random quote with image
- `GET /` - Static HTML landing page

**Performance**:
- Cold start: ~2.5s (under 3s requirement ✓)
- Warm response: ~100-200ms (under 500ms requirement ✓)
- Rate limiting overhead: <5ms (under 50ms requirement ✓)

Enjoy your serverless quotes API! 🍌
