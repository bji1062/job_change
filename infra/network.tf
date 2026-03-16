# ── VCN ──
resource "oci_core_vcn" "main" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "jobchoice-vcn"
  dns_label      = "jobchoice"
}

# ── Internet Gateway ──
resource "oci_core_internet_gateway" "igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "jobchoice-igw"
  enabled        = true
}

# ── Route Table ──
resource "oci_core_route_table" "rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "jobchoice-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.igw.id
  }
}

# ── Security List ──
resource "oci_core_security_list" "sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "jobchoice-sl"

  # SSH — 본인 IP만
  ingress_security_rules {
    protocol = "6" # TCP
    source   = var.my_ip_cidr
    tcp_options {
      min = 22
      max = 22
    }
  }

  # HTTP
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 80
      max = 80
    }
  }

  # HTTPS
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 443
      max = 443
    }
  }

  # Egress — 전체 허용
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

# ── Public Subnet ──
resource "oci_core_subnet" "public" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.main.id
  cidr_block        = "10.0.1.0/24"
  display_name      = "jobchoice-public-subnet"
  dns_label         = "pub"
  route_table_id    = oci_core_route_table.rt.id
  security_list_ids = [oci_core_security_list.sl.id]
}
