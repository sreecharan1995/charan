variable "tenant" {
  type        = string
  description = "Account Name or unique account unique id e.g., apps or management or aws007"
  default     = "spinvfx"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment area, e.g. prod or preprod "
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable  "spinvfx_vpc_name" {
  type    = string
  default = "spinvfx-vpc-prod-us-east-1"
}

variable "aws_account_id" {
  type    = string
  default = "301653940240"
}

variable "ingress_url_sslcertificate_arn" {
  type    = string
  default = "arn:aws:acm:us-east-1:301653940240:certificate/60d2972a-6c68-49b4-94ad-6e07f01765ef"
}


