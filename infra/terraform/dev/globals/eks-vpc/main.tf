#####################################################################################################################
# terraform state module                                                                                            #
# https://registry.terraform.io/modules/cloudposse/tfstate-backend/aws/latest                                       #
#####################################################################################################################

module "terraform_state_backend" {
  source     = "cloudposse/tfstate-backend/aws"
  version    = "0.38.1"
  namespace  = "spinvfx"
  stage      = "prod"
  name       = "eks-vpc"
  attributes = ["state"]

  terraform_backend_config_file_path = "."
  terraform_backend_config_file_name = "backend.tf"
  force_destroy                      = false

  terraform_version = "1.1.9"
}

#####################################################################################################################
# vpc configuration                                                                                                 #
#####################################################################################################################

data "aws_vpc" "spinvfx-net" {
   filter {
     name = "tag:Name"
     values = ["${var.spinvfx_vpc_name}"]
   }
}

data "aws_subnets" "eks-private-subnets-ids" {
  filter {
    name   = "tag:Name"
    values = ["private-subnet-eks-spin-microservices"]
  }

  depends_on = [aws_subnet.eks-private-subnets]
}

data "aws_vpc_peering_connection" "vpc-spinvfx-peering_connection" {
  filter {
    name   = "tag:Name"
    values = ["spin-test-spinvfx-net"]
  }
}

data "aws_security_groups" "eks-spinvfx-security-groups" {
  filter {
    name = "tag:aws:eks:cluster-name"
    values = ["${local.cluster_name}"]
  }
}

locals {
 eks_vpc_id = "${data.aws_vpc.spinvfx-net.id}" 
 cluster_name = "eks-spin-microservices"
}

resource "aws_subnet" "eks-public-subnets" {
 for_each = var.eks_public_subnets

 availability_zone_id                           = each.value["az"]
 vpc_id                                         = local.eks_vpc_id
 assign_ipv6_address_on_creation                = "false"
 cidr_block                                     = each.value["cidr"]
 enable_dns64                                   = "false"
 enable_resource_name_dns_a_record_on_launch    = "false"
 enable_resource_name_dns_aaaa_record_on_launch = "false"
 ipv6_native                                    = "false"
 map_public_ip_on_launch                        = "true"
 private_dns_hostname_type_on_launch            = "ip-name"

 tags = {
   Name                                           = "public-subnet-eks-spin-microservices"
   "kubernetes.io/cluster/eks-spin-microservices" = "shared"
   "kubernetes.io/role/elb"                       = "1"
 }

 tags_all = {
   Name                                           = "public-subnet-eks-spin-microservices"
   "kubernetes.io/cluster/eks-spin-microservices" = "shared"
   "kubernetes.io/role/elb"                       = "1"
 }

}

resource "aws_subnet" "eks-private-subnets" {
 for_each = var.eks_private_subnets

 availability_zone_id                           = each.value["az"]
 vpc_id                                         = local.eks_vpc_id
 assign_ipv6_address_on_creation                = "false"
 cidr_block                                     = each.value["cidr"]
 enable_dns64                                   = "false"
 enable_resource_name_dns_a_record_on_launch    = "false"
 enable_resource_name_dns_aaaa_record_on_launch = "false"
 ipv6_native                                    = "false"
 map_public_ip_on_launch                        = "false"
 private_dns_hostname_type_on_launch            = "ip-name"

 tags = {
   Name                                           = "private-subnet-eks-spin-microservices"
   "kubernetes.io/cluster/eks-spin-microservices" = "shared"
   "kubernetes.io/role/internal-elb"              = "1"
 }

 tags_all = {
   Name                                           = "private-subnet-eks-spin-microservices"
   "kubernetes.io/cluster/eks-spin-microservices" = "shared"
   "kubernetes.io/role/internal-elb"              = "1"
 }
}

resource "aws_internet_gateway" "eks-spin-microservices-igw" {
  vpc_id = local.eks_vpc_id

  tags = {
    Name = "eks-spin-microservices-igw"
  }
}

resource "aws_route_table" "route-table-eks-public-subnets" {
  vpc_id = local.eks_vpc_id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = "${aws_internet_gateway.eks-spin-microservices-igw.id}"
  }

  tags = {
    Name = "eks-spin-microservices"
  }
}

resource "aws_route_table_association" "eks-public-nets-route-assoc" {
  for_each = aws_subnet.eks-public-subnets

  subnet_id      = each.value.id
  route_table_id = "${aws_route_table.route-table-eks-public-subnets.id}"
}

resource "aws_eip" "eks_ip" {
  vpc      = true
  tags = {
    Name = "eks-spin-microservice-external-ip"
  }
}

resource "aws_nat_gateway" "eks-nat-gateway" {
  allocation_id = "${aws_eip.eks_ip.id}"
  connectivity_type = "public"
  subnet_id     = aws_subnet.eks-public-subnets[keys(aws_subnet.eks-public-subnets)[0]].id

  tags = {
    Name = "eks-nat-gateway"
  }
  depends_on = [aws_internet_gateway.eks-spin-microservices-igw]
}

data "aws_vpn_gateway" "spinvfx-vpn" {
  filter {
    name   = "tag:Name"
    values = ["SPINVFX-AWS-USEAST1-VPGW01"]
  }
} 

resource "aws_route_table" "eks-route-private-net-nat-gateway" {
  vpc_id = local.eks_vpc_id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = "${aws_nat_gateway.eks-nat-gateway.id}"
  }

  route {
    cidr_block = "192.168.0.0/16"
    gateway_id = "${data.aws_vpn_gateway.spinvfx-vpn.id}"
  }

  route {
    cidr_block = "10.0.0.0/24"
    vpc_peering_connection_id = "${data.aws_vpc_peering_connection.vpc-spinvfx-peering_connection.id}"
  }

  tags = {
    Name = "eks_route_private_net_nat_gateway"
  }
}

resource "aws_route_table_association" "eks-private-nets-route-assoc" {
  for_each = aws_subnet.eks-private-subnets

  subnet_id      = each.value.id
  route_table_id = aws_route_table.eks-route-private-net-nat-gateway.id
}
