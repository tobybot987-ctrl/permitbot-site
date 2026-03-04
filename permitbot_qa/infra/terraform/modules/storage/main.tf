resource "aws_s3_bucket" "permitbot" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_versioning" "permitbot" {
  bucket = aws_s3_bucket.permitbot.id
  versioning_configuration {
    status = "Enabled"
  }
}

output "bucket_name" {
  value = aws_s3_bucket.permitbot.bucket
}
