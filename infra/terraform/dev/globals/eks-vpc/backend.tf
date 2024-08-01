terraform {
  required_version = ">= 1.1.9"

  backend "s3" {
    region         = "us-east-1"
    bucket         = "spinvfx-prod-eks-vpc-state"
    key            = "terraform.tfstate"
    dynamodb_table = "spinvfx-prod-eks-vpc-state-lock"
    profile        = ""
    role_arn       = ""
    encrypt        = "true"
  }
}
