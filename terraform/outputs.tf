output "public_dns" {
  value       = aws_instance.app.public_dns
  description = "Open this URL in your browser after deployment"
}

output "application_url" {
  value       = "http://${aws_instance.app.public_dns}"
  description = "Direct link to the simulator"
}

output "instance_id" {
  value = aws_instance.app.id
}

output "ssh_instruction" {
  value = "Connect using AWS Systems Manager Session Manager (no key needed)"
}
