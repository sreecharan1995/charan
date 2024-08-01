provider "aws" {
  region = "us-east-1"
}

module "ecr" {
  source    = "cloudposse/ecr/aws"  
  version   = "0.35.0"
  namespace = "spinfx"
  stage     = "prod"
  name      = "ecr"
  force_delete = "true"
  
  image_tag_mutability = "MUTABLE"
  image_names = [ "rez-service", "web-portal", "backend-services", "scheduler-jobs" ]
  # principals_full_access = [data.aws_iam_role.ecr.arn]

  tags = {
    env   = "dev"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }
}

# Module to create remote state
module "terraform_state_backend" {
  source = "cloudposse/tfstate-backend/aws"
  version     = "0.38.1"
  namespace  = "spinfx"
  stage      = "prod"
  name       = "ecr"
  attributes = ["state"]

  terraform_backend_config_file_path = "."
  terraform_backend_config_file_name = "backend.tf"
  force_destroy                      = false

  terraform_version = "0.13.1"
}


####################################################################
# Local variables                                                  #
####################################################################

locals {
  aws_account_id  = var.aws_account_id
}

####################################################################
# IAM Resources                                                    #
####################################################################

resource "aws_iam_user" "ecr-user" {
  force_destroy = "false"
  name          = "ecr"
  path          = "/"

  tags = {
    env   = "dev"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }

  tags_all = {
    env   = "dev"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }
}

resource "aws_iam_user_policy_attachment" "ecr-user-polity-attach" {
  policy_arn = "arn:aws:iam::${local.aws_account_id}:policy/ECRFullAccess"
  user       = "ecr"
}


resource "aws_iam_policy" "ecr-user-policy" {
  description = "Temporary policy"
  name        = "ECRFullAccess"
  path        = "/"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "ecr:GetRegistryPolicy",
        "ecr:CreateRepository",
        "ecr:DescribeRegistry",
        "ecr:DescribePullThroughCacheRules",
        "ecr:GetAuthorizationToken",
        "ecr:PutRegistryScanningConfiguration",
        "ecr:CreatePullThroughCacheRule",
        "ecr:DeletePullThroughCacheRule",
        "ecr:PutRegistryPolicy",
        "ecr:GetRegistryScanningConfiguration",
        "ecr:BatchImportUpstreamImage",
        "ecr:DeleteRegistryPolicy",
        "ecr:PutReplicationConfiguration"
      ],
      "Effect": "Allow",
      "Resource": "*",
      "Sid": "VisualEditor0"
    },
    {
      "Action": "ecr:*",
      "Effect": "Allow",
      "Resource": "arn:aws:ecr:*:${local.aws_account_id}:repository/*",
      "Sid": "VisualEditor1"
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  tags = {
    env   = "test"
    owner = "ernesto"
  }

  tags_all = {
    env   = "test"
    owner = "ernesto"
  }
}
