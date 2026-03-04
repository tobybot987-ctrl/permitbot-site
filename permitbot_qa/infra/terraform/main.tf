terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "storage" {
  source      = "./modules/storage"
  bucket_name = var.s3_bucket_name
}

module "queue" {
  source = "./modules/queue"
  name   = var.project_name
}

output "s3_bucket" {
  value = module.storage.bucket_name
}

output "sqs_ingest_queue_url" {
  value = module.queue.ingest_queue_url
}

output "sqs_check_queue_url" {
  value = module.queue.check_queue_url
}
