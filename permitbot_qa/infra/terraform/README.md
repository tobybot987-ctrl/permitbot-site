# AWS Baseline (Phase 1.5)

This Terraform baseline provisions long-term production primitives for PermitBot QA:

- VPC + subnets (module: `network`)
- S3 bucket for packs/uploads/reports (module: `storage`)
- RDS Postgres for run metadata (module: `database`)
- SQS queues for async jobs (module: `queue`)
- ECS/Fargate service scaffold (module: `compute`)

## Deployment order
1. `network`
2. `storage` + `queue`
3. `database`
4. `compute`

## Required AWS inputs
- AWS account + IAM with Terraform apply permissions
- Route53 zone (optional for API domain)
- ACM cert (if ALB HTTPS)

## Runtime env expected by app
- `AWS_REGION`
- `S3_BUCKET`
- `S3_PREFIX` (default `permitbot`)
- `DATABASE_URL`
- `SQS_INGEST_QUEUE_URL`
- `SQS_CHECK_QUEUE_URL`
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` (or IAM role)
