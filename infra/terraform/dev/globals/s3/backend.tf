terraform {
  required_version = ">= 1.1.9"

  backend "s3" {
    region         = "us-east-1"
    bucket         = "spinfx-dev-levels-tree-dev-state"
    key            = "terraform.tfstate"
    dynamodb_table = "spinfx-dev-levels-tree-dev-state-lock"
    profile        = ""
    role_arn       = ""
    encrypt        = "true"
  }
}
