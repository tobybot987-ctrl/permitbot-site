resource "aws_sqs_queue" "ingest" {
  name = "${var.name}-ingest"
}

resource "aws_sqs_queue" "check" {
  name = "${var.name}-check"
}

output "ingest_queue_url" {
  value = aws_sqs_queue.ingest.id
}

output "check_queue_url" {
  value = aws_sqs_queue.check.id
}
