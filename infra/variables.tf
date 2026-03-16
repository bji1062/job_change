# ── OCI 인증 ──
variable "tenancy_ocid" {
  description = "OCI Tenancy OCID"
}

variable "user_ocid" {
  description = "OCI User OCID"
}

variable "compartment_ocid" {
  description = "OCI Compartment OCID (리소스 생성 위치)"
}

variable "fingerprint" {
  description = "API Key fingerprint"
}

variable "private_key_path" {
  description = "OCI API private key 파일 경로"
}

variable "region" {
  default     = "ap-chuncheon-1"
  description = "OCI region (춘천)"
}

# ── SSH ──
variable "ssh_public_key" {
  description = "SSH public key for instance access"
}

# ── 인스턴스 ──
variable "instance_shape" {
  default     = "VM.Standard.A1.Flex"
  description = "Always Free ARM instance shape"
}

variable "instance_ocpus" {
  default     = 2
  description = "OCPU 수 (Always Free 최대 4)"
}

variable "instance_memory_gb" {
  default     = 12
  description = "메모리 GB (Always Free 최대 24, OCPU당 최대 6)"
}

variable "boot_volume_gb" {
  default     = 50
  description = "부트 볼륨 크기 (Always Free 최대 200GB)"
}

variable "my_ip_cidr" {
  description = "SSH 접근 허용 IP (e.g. 1.2.3.4/32)"
}
