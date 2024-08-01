terraform {
  required_version = ">= 1.1.9"

  backend "s3" {
    region         = "us-east-1"
    bucket         = "spinfx-dev-dynamodb-state"
    key            = "terraform.tfstate"
    dynamodb_table = "spinfx-dev-dynamodb-state-lock"
    profile        = ""
    role_arn       = ""
    encrypt        = "true"
  }
}
