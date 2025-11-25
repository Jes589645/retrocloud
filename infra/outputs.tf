output "main_instance_public_ip" {
  value       = aws_instance.main.public_ip
  description = "IP pública de la instancia principal"
}

output "main_instance_public_dns" {
  value       = aws_instance.main.public_dns
  description = "DNS público de la instancia principal"
}
