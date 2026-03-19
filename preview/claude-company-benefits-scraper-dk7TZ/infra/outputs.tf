output "public_ip" {
  description = "Public IP of the jobchoice server"
  value       = oci_core_instance.app.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to the server"
  value       = "ssh ubuntu@${oci_core_instance.app.public_ip}"
}

output "instance_id" {
  description = "OCI instance OCID"
  value       = oci_core_instance.app.id
}

output "instance_shape" {
  description = "Instance shape and config"
  value       = "${var.instance_shape} (${var.instance_ocpus} OCPU, ${var.instance_memory_gb}GB RAM)"
}
