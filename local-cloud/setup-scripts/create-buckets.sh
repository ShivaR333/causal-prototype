#!/bin/bash
set -e

echo "Creating S3 buckets..."

# Create raw data bucket
awslocal s3 mb s3://causal-analysis-dev-rawdata
awslocal s3api put-bucket-versioning \
    --bucket causal-analysis-dev-rawdata \
    --versioning-configuration Status=Enabled

# Create artifacts bucket
awslocal s3 mb s3://causal-analysis-dev-artifacts
awslocal s3api put-bucket-versioning \
    --bucket causal-analysis-dev-artifacts \
    --versioning-configuration Status=Enabled

# Set bucket policies for security
awslocal s3api put-public-access-block \
    --bucket causal-analysis-dev-rawdata \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

awslocal s3api put-public-access-block \
    --bucket causal-analysis-dev-artifacts \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enable encryption
awslocal s3api put-bucket-encryption \
    --bucket causal-analysis-dev-rawdata \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

awslocal s3api put-bucket-encryption \
    --bucket causal-analysis-dev-artifacts \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

# Create lifecycle rules for cost optimization
awslocal s3api put-bucket-lifecycle-configuration \
    --bucket causal-analysis-dev-artifacts \
    --lifecycle-configuration '{
        "Rules": [{
            "ID": "delete-old-artifacts",
            "Status": "Enabled",
            "Expiration": {
                "Days": 30
            },
            "NoncurrentVersionExpiration": {
                "NoncurrentDays": 7
            }
        }]
    }'

# Upload sample data files
echo "Uploading sample data..."
for file in /app/data/sample_data/*.csv; do
    if [ -f "$file" ]; then
        awslocal s3 cp "$file" s3://causal-analysis-dev-rawdata/sample_data/
    fi
done

echo "S3 buckets created and configured successfully!"