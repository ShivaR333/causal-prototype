output "rawdata_bucket_name" {
  description = "Name of the raw data S3 bucket"
  value       = aws_s3_bucket.rawdata.id
}

output "rawdata_bucket_arn" {
  description = "ARN of the raw data S3 bucket"
  value       = aws_s3_bucket.rawdata.arn
}

output "artifacts_bucket_name" {
  description = "Name of the artifacts S3 bucket"
  value       = aws_s3_bucket.artifacts.id
}

output "artifacts_bucket_arn" {
  description = "ARN of the artifacts S3 bucket"
  value       = aws_s3_bucket.artifacts.arn
}