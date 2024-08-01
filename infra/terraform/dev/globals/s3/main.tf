provider "aws" {
  region = var.region
}


#####################################################################################################################
# terraform state module                                                                                            #
# https://registry.terraform.io/modules/cloudposse/tfstate-backend/aws/latest                                       #
#####################################################################################################################

module "terraform_state_backend" {
  source     = "cloudposse/tfstate-backend/aws"
  version    = "0.38.1"
  namespace  = "spinfx"
  stage      = "dev"
  name       = "levels-tree-dev"
  attributes = ["state"]

  terraform_backend_config_file_path = "."
  terraform_backend_config_file_name = "backend.tf"
  force_destroy                      = false

  terraform_version = "1.1.9"
}

########################################################################
# levels-tree  volumes                                                 #
########################################################################

module "s3" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "3.4.0"

  bucket = "levels-tree-dev"

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true  

  tags = {
    env   = "dev"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }

}

# bucket for dev environment levels-tree-sync app volume 
module "levels-tree-uat" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "3.4.0"

  bucket = "levels-tree-uat"

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  tags = {
    env   = "uat"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }
}

module "levels-tree-prod" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "3.4.0"

  bucket = "levels-tree-prod"

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  tags = {
    env   = "uat"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }
}

########################################################################
# configurations    volumes                                            #
########################################################################

module "configs-configurations-dev" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "3.4.0"

  bucket = "configs-configurations-dev"

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  tags = {
    env   = "uat"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }
}

module "configs-configurations-uat" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "3.4.0"

  bucket = "configs-configurations-uat"

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  tags = {
    env   = "uat"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }
}

module "configs-configurations-prod" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "3.4.0"

  bucket = "configs-configurations-prod"

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  tags = {
    env   = "uat"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }
}

########################################################################
# permission matrix volumes                                            #
########################################################################

module "permission-matrix-uat" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "3.4.0"

  bucket = "uat-permission-matrix"

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  versioning = {
    enabled = true
  }

  tags = {
    env   = "uat"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }
}

module "permission-matrix-prod" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "3.4.0"

  bucket = "prod-permission-matrix"

  versioning = {
    enabled = true
  }

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  tags = {
    env   = "prod"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }
}


########################################################################
# spin-rez volumes                                                     #
########################################################################

module "spin-rez-prod" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "3.4.0"

  bucket = "spin-rez-prod"

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  tags = {
    env   = "prod"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }
}

########################################################################
# SG Event Scripts volumes                                             #
########################################################################
module "dev-sg-event-scripts" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "3.4.0"

  bucket = "dev-sg-event-scripts"

  versioning = {
    enabled = true
  }

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  tags = {
    env   = "dev"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }
}

module "uat-sg-event-scripts" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "3.4.0"

  bucket = "uat-sg-event-scripts"

  versioning = {
    enabled = true
  }

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  tags = {
    env   = "dev"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }
}

module "prod-sg-event-scripts" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "3.4.0"

  bucket = "prod-sg-event-scripts"

  versioning = {
    enabled = true
  }

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  tags = {
    env   = "dev"
    owner = "rocketpad"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }
}