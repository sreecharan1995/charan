terraform {
  required_version = ">= 0.13.1"

  backend "s3" {
    region         = "us-east-1"
    bucket         = "spinfx-prod-ecr-state"
    key            = "terraform.tfstate"
    dynamodb_table = "spinfx-prod-ecr-state-lock"
    profile        = ""
    role_arn       = ""
    encrypt        = "true"
  }
}
