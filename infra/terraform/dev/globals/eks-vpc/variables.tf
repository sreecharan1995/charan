variable  "region" {
  type    = string
  default = "us-east-1"
}

variable  "spinvfx_vpc_name" {
  type    = string
  default = "spinvfx-vpc-prod-us-east-1"
}

variable "eks_public_subnets" {
   type = map
   default = {
      sub-1 = {
         az = "use1-az2"
         cidr = "10.98.200.0/24"
      }
      sub-2 = {
         az = "use1-az4"
         cidr = "10.98.201.0/24"
      }
      sub-3 = {
         az = "use1-az6"
         cidr = "10.98.202.0/24"
      }
   }
}

variable "eks_private_subnets" {
   type = map
   default = {
      sub-1 = {
         az = "use1-az2"
         cidr = "10.98.190.0/24"
      }
      sub-2 = {
         az = "use1-az4"
         cidr = "10.98.191.0/24"
      }
      sub-3 = {
         az = "use1-az6"
         cidr = "10.98.192.0/24"
      }
   }
}
