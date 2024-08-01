provider "aws" {
  region = "us-east-1"
}


#####################################################################################################################
# terraform state module                                                                                                   #
# https://registry.terraform.io/modules/cloudposse/tfstate-backend/aws/latest
#####################################################################################################################

module "terraform_state_backend" {
  source     = "cloudposse/tfstate-backend/aws"
  version    = "0.38.1"
  namespace  = "spinfx"
  stage      = "dev"
  name       = "dynamodb"
  attributes = ["state"]

  terraform_backend_config_file_path = "."
  terraform_backend_config_file_name = "backend.tf"
  force_destroy                      = false

  terraform_version = "1.1.9"
}


module "dynamodb_table" {
  source   = "terraform-aws-modules/dynamodb-table/aws"

  name      = "dependency-service"
  hash_key  = "id"

  attributes = [
    {
      name = "id"
      type = "N"
    }
  ]

  tags = {
    env = "dev"
  }
}

resource "aws_iam_user" "dynamodb_dev_iam_user" {
  force_destroy = "false"
  name          = "dynamodb-user"
  path          = "/"

  tags = {
    env   = "dev"
    owner = "rocketpad"
  }

  tags_all = {
    env   = "dev"
    owner = "rocketpad"
  }
}

resource "aws_iam_user_policy_attachment" "dynamodb_dev_iam_user_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
  user       = "dynamodb-user"
}
