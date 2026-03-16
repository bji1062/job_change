variable "region" {
  default     = "ap-northeast-2"
  description = "AWS region (Seoul)"
}

variable "ssh_public_key" {
  description = "SSH public key for instance access"
}

variable "instance_type" {
  default     = "t4g.small"
  description = "EC2 instance type (Graviton ARM)"
}

variable "my_ip_cidr" {
  description = "Your IP CIDR for SSH access (e.g. 1.2.3.4/32)"
}

variable "volume_size_gb" {
  default     = 50
  description = "Root EBS volume size in GB"
}
