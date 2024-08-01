provider "aws" {
  region = local.region
}

#####################################################################################################################
# terraform state module                                                                                                   #
# https://registry.terraform.io/modules/cloudposse/tfstate-backend/aws/latest
#####################################################################################################################

module "terraform_state_backend" {
  source     = "cloudposse/tfstate-backend/aws"
  version    = "0.38.1"
  namespace  = "spinvfx"
  stage      = "prod"
  name       = "eks-spin-microservices"
  attributes = ["state"]

  terraform_backend_config_file_path = "."
  terraform_backend_config_file_name = "backend.tf"
  force_destroy                      = false

  terraform_version = "1.1.9"
}

#####################################################################################################################
# Initializing kubernetes providers and tools                                                                       #
#####################################################################################################################

provider "kubernetes" {
  host                   = module.eks_blueprints.eks_cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks_blueprints.eks_cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1"
    command     = "aws"
    # This requires the awscli to be installed locally where Terraform is executed
    args = ["eks", "get-token", "--cluster-name", module.eks_blueprints.eks_cluster_id]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks_blueprints.eks_cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks_blueprints.eks_cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1"
      command     = "aws"
      # This requires the awscli to be installed locally where Terraform is executed
      args = ["eks", "get-token", "--cluster-name", module.eks_blueprints.eks_cluster_id]
    }
  }
}

provider "kubectl" {
  host                   = module.eks_blueprints.eks_cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks_blueprints.eks_cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1alpha1"
    command     = "aws"
    # This requires the awscli to be installed locally where Terraform is executed
    args = ["eks", "get-token", "--cluster-name", module.eks_blueprints.eks_cluster_id]
  }
  load_config_file = false
}

locals {
  tenant          = var.tenant      # AWS account name or unique id for tenant
  environment     = var.environment # Environment area eg., preprod or prod
  region          = var.region
  aws_account_id  = var.aws_account_id

  cluster_name    = "eks-spin-microservices"
  cluster_version = "1.24"

  eks_vpc_id = "${data.aws_vpc.spinvfx-net.id}"
  eks_private_subnets_ids = "${data.aws_subnets.eks-private-subnets-ids.ids}"
  eks_security_groups_ids = data.aws_security_groups.eks-spinvfx-security-groups.ids 

  tags = {
    env  = "dev"
    owner = "rocketpad"
    eks_version = "1.24"
    d-server-03cruxb0n03orf="d-server-03cruxb0n03orf"
  }
}

#####################################################################################################################
# EKS VPC                                                                                                          #
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
}

data "aws_security_groups" "eks-spinvfx-security-groups" {
  filter {
    name   = "tag:aws:eks:cluster-name"
    values = ["${local.cluster_name}"]
  }
}

#####################################################################################################################
# EKS Cluster configuration using AWS Blueprint terraform module                                                    #
# https://github.com/aws-ia/terraform-aws-eks-blueprints                                                            # 
#####################################################################################################################

module "eks_blueprints" {
  source = "github.com/aws-ia/terraform-aws-eks-blueprints?ref=v4.26.0"

  # EKS Cluster Name
  cluster_name = local.cluster_name

  # EKS Cluster VPC and Subnet mandatory config
  vpc_id                  = local.eks_vpc_id
  private_subnet_ids      = local.eks_private_subnets_ids

  # EKS CONTROL PLANE VARIABLES
  cluster_version = local.cluster_version

  # EKS MANAGED NODE GROUPS
  # m5.large (allow 29 pods as per https://github.com/awslabs/amazon-eks-ami/blob/master/files/eni-max-pods.txt)
  managed_node_groups = {
    ng_dev = {
      node_group_name = "managed-spot"
      instance_types  = ["t3.large","t3.xlarge"] # ["m5.large","m4.large","m5a.large"]
      capacity_type   = "SPOT"

      min_size     = 3
      desired_size = 3
      max_size     = 4

      k8s_labels = {
        Environment = "dev"
      }

      subnet_ids = local.eks_private_subnets_ids # module.aws_vpc.private_subnets
    }

    ng_prod = {
      node_group_name = "managed-prod"
      instance_types  = ["t2.medium", "t3.medium"] # ["m5.large","m4.large","m5a.large"]
      capacity_type   = "ON_DEMAND"

      min_size     = 1
      desired_size = 2
      max_size     = 3

      k8s_labels = {
        Environment = "prod"
      }

      subnet_ids = local.eks_private_subnets_ids # module.aws_vpc.private_subnets
    }
  }

  #List of map_roles
  map_roles = [
    {
      rolearn  = "arn:aws:iam::${local.aws_account_id}:role/dev-role-developer"   # The ARN of the IAM role
      username = "dev-role-developer"                                  # The user name within Kubernetes to map to the IAM role
      groups   = ["developers"]                                        # A list of groups within Kubernetes to which the role is mapped; Checkout K8s Role and Rolebindings
    }
  ]

  # Add Iam users to the EKS Cluster
  map_users = [
    {
      userarn  = "arn:aws:iam::${local.aws_account_id}:user/edovale@huru.io"   # The ARN of the IAM user to add.
      username = "edovale"                                          # The user name within Kubernetes to map to the IAM role
      groups   = ["system:masters"]                                 # A list of groups within Kubernetes to which the role is mapped; Checkout K8s Role and Rolebindings
    },
    {
      userarn  = "arn:aws:iam::${local.aws_account_id}:user/test-access"   # The ARN of the IAM user to add.
      username = "test-access"                                  # The user name within Kubernetes to map to the IAM role
      groups   = ["Readonly-Group"]                             # A list of groups within Kubernetes to which the role is mapped; Checkout K8s Role and Rolebindings
    },
    {
      userarn  = "arn:aws:iam::${local.aws_account_id}:user/adantu@spinvfx.com"   # The ARN of the IAM user to add.
      username = "adantu"                                              # The user name within Kubernetes to map to the IAM role
      groups   = ["system:masters"]                                    # A list of groups within Kubernetes to which the role is mapped; Checkout K8s Role and Rolebindings
    },
    {
      userarn  = "arn:aws:iam::${local.aws_account_id}:user/hsidhu@spinvfx.com"   # The ARN of the IAM user to add.
      username = "hsidhu"                                              # The user name within Kubernetes to map to the IAM role
      groups   = ["system:masters"]                                    # A list of groups within Kubernetes to which the role is mapped; Checkout K8s Role and Rolebindings
    },
    {
      userarn  = "arn:aws:iam::${local.aws_account_id}:user/vnanavati@spinvfx.com"   # The ARN of the IAM user to add.
      username = "vnanavati"                                              # The user name within Kubernetes to map to the IAM role
      groups   = ["system:masters"]                                       # A list of groups within Kubernetes to which the role is mapped; Checkout K8s Role and Rolebindings
    },
    {
      userarn  = "arn:aws:iam::${local.aws_account_id}:user/scharan@spinvfx.com"     # The ARN of the IAM user to add.
      username = "scharan"                                                # The user name within Kubernetes to map to the IAM role
      groups   = ["system:masters"]                                       # A list of groups within Kubernetes to which the role is mapped; Checkout K8s Role and Rolebindings
    }
  ]

  tags = local.tags

}

module "eks_blueprints_kubernetes_addons" {
  source         = "github.com/aws-ia/terraform-aws-eks-blueprints//modules/kubernetes-addons?ref=v4.26.0"
  eks_cluster_id = module.eks_blueprints.eks_cluster_id

  # EKS Managed Add-ons
  enable_amazon_eks_vpc_cni = true
  amazon_eks_vpc_cni_config = {
    addon_version     = "v1.12.6-eksbuild.1"
    resolve_conflicts = "OVERWRITE"
  }
  enable_amazon_eks_coredns    = true
  enable_amazon_eks_kube_proxy = true

  #K8s Add-ons
  enable_metrics_server         = true
  enable_cluster_autoscaler     = true
  enable_ingress_nginx          = false
  
  enable_aws_load_balancer_controller = true
  aws_load_balancer_controller_helm_config = {
    version = "1.4.2"
  }

  enable_aws_cloudwatch_metrics        = true
  # aws_cloudwatch_metrics_irsa_policies = ["IAM Policies"]
  aws_cloudwatch_metrics_helm_config   = {
    name       = "aws-cloudwatch-metrics"
    chart      = "aws-cloudwatch-metrics"
    repository = "https://aws.github.io/eks-charts"
    version    = "0.0.7"
    namespace  = "amazon-cloudwatch"
    values     = [templatefile("${path.module}/kubernetes/modules_addons/monitoring/aws_cloudwatch_metrics_values.yaml", {
      eks_cluster_id = module.eks_blueprints.eks_cluster_id
    })]
  }

  enable_aws_for_fluentbit = true
  # aws_for_fluentbit_irsa_policies = ["IAM Policies"] # Add list of additional policies to IRSA to enable access to Kinesis, OpenSearch etc.
  aws_for_fluentbit_cw_log_group_retention = 90
  aws_for_fluentbit_helm_config = {
    name                                      = "aws-for-fluent-bit"
    chart                                     = "aws-for-fluent-bit"
    repository                                = "https://aws.github.io/eks-charts"
    version                                   = "0.1.23"
    namespace                                 = "fluent-bit"
    #aws_for_fluent_bit_cw_log_group           = "/${local.cluster_id}/worker-fluentbit-logs" # Optional
    create_namespace                          = true
    values = [templatefile("${path.module}/kubernetes/modules_addons/monitoring/fluentbit_values.yaml", {
      region                          = local.region
    })]
  }

  depends_on = [module.eks_blueprints.managed_node_groups]
}

#####################################################################################################################
# Install csi-driver-nfs                                                                                            #
#####################################################################################################################
resource "helm_release" "nfs_client" {
  name = "csi-driver-nfs"
  repository = "https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts"
  chart = "csi-driver-nfs"
  version = "4.2.0"
  namespace = "kube-system"
  set { 
    name = "nfs.server"
    value= "tor-hspace.spinvfx.com"
  }
  set { 
    name = "nfs.path"
    value= "/spin"
  }
}

#####################################################################################################################
# Create pv and pvc for permission-matrix folder                                                                    #
#####################################################################################################################

data "kubectl_filename_list" "permission_matrix_files" {
  pattern = "./kubernetes/storage/nfs/permission-matrix/*.yaml"
}

resource "kubectl_manifest" "inject_permission_matrix" {
  count     = length(data.kubectl_filename_list.permission_matrix_files.matches)
  yaml_body = file(element(data.kubectl_filename_list.permission_matrix_files.matches, count.index))
}

#####################################################################################################################
# Create pv and pvc for configs-configurations folder                                                               #
#####################################################################################################################

data "kubectl_filename_list" "configs_configurations_files" {
  pattern = "./kubernetes/storage/nfs/configs-configurations/*.yaml"
}

resource "kubectl_manifest" "inject_configs_configurations" {
  count     = length(data.kubectl_filename_list.configs_configurations_files.matches)
  yaml_body = file(element(data.kubectl_filename_list.configs_configurations_files.matches, count.index))
}

#####################################################################################################################
# Create pv and pvc for sg-event-scripts folder                                                                    #
#####################################################################################################################

data "kubectl_filename_list" "sg-event-scripts_files" {
  pattern = "./kubernetes/storage/nfs/sg-event-scripts/*.yaml"
}

resource "kubectl_manifest" "inject_sg-event-scripts" {
  count     = length(data.kubectl_filename_list.sg-event-scripts_files.matches)
  yaml_body = file(element(data.kubectl_filename_list.sg-event-scripts_files.matches, count.index))
}

#####################################################################################################################
# Create pv and pvc for levels-tree folder                                                                          #
#####################################################################################################################

data "kubectl_filename_list" "levels_tree_files" {
  pattern = "./kubernetes/storage/nfs/levels-tree/*.yaml"
}

resource "kubectl_manifest" "inject_levels_tree" {
  count     = length(data.kubectl_filename_list.levels_tree_files.matches)
  yaml_body = file(element(data.kubectl_filename_list.levels_tree_files.matches, count.index))
}

#####################################################################################################################
# Create pv and pvc for spin-rez    folder                                                                          #
#####################################################################################################################

data "kubectl_filename_list" "spin_rez_files" {
  pattern = "./kubernetes/storage/nfs/spin-rez/*.yaml"
}

resource "kubectl_manifest" "inject_spin_rez" {
  count     = length(data.kubectl_filename_list.spin_rez_files.matches)
  yaml_body = file(element(data.kubectl_filename_list.spin_rez_files.matches, count.index))
}

#####################################################################################################################
# Create pv and pvc for ms_k8_job_shared folder                                                                     #
#####################################################################################################################

data "kubectl_filename_list" "ms_k8_job_shared_files" {
  pattern = "./kubernetes/storage/nfs/ms_k8_job_shared/*.yaml"
}

resource "kubectl_manifest" "inject_ms_k8_job_shared" {
  count     = length(data.kubectl_filename_list.ms_k8_job_shared_files.matches)
  yaml_body = file(element(data.kubectl_filename_list.ms_k8_job_shared_files.matches, count.index))
}

#####################################################################################################################
# Create pv and pvc for spin shared folder                                                                          #
#####################################################################################################################

data "kubectl_filename_list" "spin_shared" {
  pattern = "./kubernetes/storage/nfs/spin/*.yaml"
}

resource "kubectl_manifest" "inject_spin_shared_files" {
  count     = length(data.kubectl_filename_list.spin_shared.matches)
  yaml_body = file(element(data.kubectl_filename_list.spin_shared.matches, count.index))
}

#####################################################################################################################
# Ingress manifests internal                                                                                        #
#####################################################################################################################

data "kubectl_filename_list" "Ingress_internal_files" {
  pattern = "./kubernetes/ingress/internal/*.yaml"
}

resource "kubectl_manifest" "inject_Ingress_internal" {
  count     = length(data.kubectl_filename_list.Ingress_internal_files.matches)
  yaml_body = file(element(data.kubectl_filename_list.Ingress_internal_files.matches, count.index))
}

#####################################################################################################################
# Ingress manifests                                                                                                 #
#####################################################################################################################

data "kubectl_filename_list" "ingress_files_v2" {
  pattern = "kubernetes/ingress/*.yaml"
}

resource "null_resource" "execute_ingress_files_v2" {
  for_each = toset(data.kubectl_filename_list.ingress_files_v2.matches)
  
  triggers = {
    file_modified = sha1(join("", [for f in fileset("kubernetes/ingress", "*.yaml"): filesha1("kubernetes/ingress/${f}")]))
  }

  provisioner "local-exec" {
   command = "envsubst < ${each.value} | kubectl apply -f -"
   environment = {
      CERT = "${var.ingress_url_sslcertificate_arn}"
    }
  }
}

#####################################################################################################################
# Ingress manifests                                                                                                 #
#####################################################################################################################

#data "kubectl_filename_list" "Ingress_files" {
#  pattern = "./kubernetes/ingress/*.yaml"
#}
#
#resource "kubectl_manifest" "inject_Ingress" {
#  count     = length(data.kubectl_filename_list.Ingress_files.matches)
#  yaml_body = file(element(data.kubectl_filename_list.Ingress_files.matches, count.index))
#}

#####################################################################################################################
# Namespaces EKS                                                                                                    #
#####################################################################################################################

data "kubectl_filename_list" "Namespaces_files" {
  pattern = "./kubernetes/namespaces/*.yaml"
}

resource "kubectl_manifest" "inject_namespaces" {
  count     = length(data.kubectl_filename_list.Namespaces_files.matches)
  yaml_body = file(element(data.kubectl_filename_list.Namespaces_files.matches, count.index))
}

#####################################################################################################################
# RBAC EKS                                                                                                          #
#####################################################################################################################

data "kubectl_filename_list" "RBAC_files" {
  pattern = "./kubernetes/rbac/*.yaml"
}

resource "kubectl_manifest" "inject_RBAC" {
  count     = length(data.kubectl_filename_list.RBAC_files.matches)
  yaml_body = file(element(data.kubectl_filename_list.RBAC_files.matches, count.index))
}

data "kubectl_filename_list" "RBAC_user_access_files" {
  pattern = "./kubernetes/rbac/user-access/*.yaml"
}

resource "kubectl_manifest" "inject_user_access_RBAC" {
  count     = length(data.kubectl_filename_list.RBAC_user_access_files.matches)
  yaml_body = file(element(data.kubectl_filename_list.RBAC_user_access_files.matches, count.index))
}

#####################################################################################################################
# User for deployment from bitbucket pipeline                                                                       #
#####################################################################################################################

resource "aws_iam_user" "kubectl_dev_user" {
  count = 0
  force_destroy = "false"
  name          = "kubectl_dev_user"
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

resource "aws_iam_policy" "dev-role-developer_policy" {
  count = 1
  description = "Role to allow deploy to EKS "
  name        = "dev-role-developer"
  path        = "/"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "eks:AccessKubernetesApi",
        "eks:Describe*",
        "eks:List*"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  tags = {
    env   = "dev"
    owner = "rocketpad"
  }

  tags_all = {
    env   = "dev"
    owner = "rocketpad"
  }
}

resource "aws_iam_role" "kubectl_dev_user-assume-dev-role-developer" {
 count = 1  
 assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${local.aws_account_id}:user/kubectl_dev_user"
      },
      "Sid": "EKSClusterAssumeRole"
    }
  ],
  "Version": "2012-10-17"
}
POLICY
  managed_policy_arns  = ["arn:aws:iam::${local.aws_account_id}:policy/dev-role-developer"]
  max_session_duration = "3600"
  name                 = "dev-role-developer"
  path                 = "/"
  tags = {
    env   = "dev"
    owner = "rocketpad"
  }
  tags_all = {
    env   = "dev"
    owner = "rocketpad"
  }
}

resource "aws_iam_user_policy_attachment" "kubectl_dev_user-policy_attachment" {
  count = 1
  policy_arn = "arn:aws:iam::${local.aws_account_id}:policy/dev-role-developer"
  user       = "kubectl_dev_user"
}

#####################################################################################################################
# Lambda function to relay event to api endpoints                                                                   #
#####################################################################################################################
module "lambda_dependency_api_relay" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.6.1"

  function_name = "lambda_dependency_api_relay"
  description   = "Lambda relay to dependency-service api endpoint"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"

  environment_variables = {
    request_url = "http://dependencies-internal.dev.spinvfx.com/on-validity-change"
    request_http_method = "PUT"
  }
  
  source_path = "./lambda-relays/lambda-request-relay"

  vpc_subnet_ids         = local.eks_private_subnets_ids
  vpc_security_group_ids = local.eks_security_groups_ids
  attach_network_policy  = true

  tags = local.tags
}

module "lambda_rez_api_relay" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.6.1"

  function_name = "lambda_rez_api_relay"
  description   = "Lambda relay to rez-service api endpoint"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"

  environment_variables = {
    request_url = "http://rez-service-internal.dev.spinvfx.com/on-event"
    request_http_method = "POST"
  }

  source_path = "./lambda-relays/lambda-request-relay"

  vpc_subnet_ids         = local.eks_private_subnets_ids
  vpc_security_group_ids = local.eks_security_groups_ids  
  attach_network_policy  = true

  tags = local.tags
}

module "lambda_dependency_api_relay_uat" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.6.1"

  function_name = "lambda_dependency_api_relay_uat"
  description   = "Lambda relay to dependency-service api endpoint - uat"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"

  environment_variables = {
    request_url = "http://dependencies-internal-uat.dev.spinvfx.com/on-validity-change"
    request_http_method = "PUT"
  }

  source_path = "./lambda-relays/lambda-request-relay"

  vpc_subnet_ids         = local.eks_private_subnets_ids
  vpc_security_group_ids = local.eks_security_groups_ids
  attach_network_policy  = true

  tags = local.tags
}

module "lambda_rez_api_relay_uat" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.6.1"

  function_name = "lambda_rez_api_relay_uat"
  description   = "Lambda relay to rez-service api endpoint - uat"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"

  environment_variables = {
    request_url = "http://rez-service-internal-uat.dev.spinvfx.com/on-event"
    request_http_method = "POST"
  }

  source_path = "./lambda-relays/lambda-request-relay"

  vpc_subnet_ids         = local.eks_private_subnets_ids
  vpc_security_group_ids = local.eks_security_groups_ids
  attach_network_policy  = true

  tags = local.tags
}

module "lambda_dependency_api_relay_prod" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.6.1"

  function_name = "lambda_dependency_api_relay_prod"
  description   = "Lambda relay to dependency-service api endpoint - prod"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"

  environment_variables = {
    request_url = "http://dependencies-internal-prod.dev.spinvfx.com/on-validity-change"
    request_http_method = "PUT"
  }

  source_path = "./lambda-relays/lambda-request-relay"

  vpc_subnet_ids         = local.eks_private_subnets_ids
  vpc_security_group_ids = local.eks_security_groups_ids
  attach_network_policy  = true

  tags = local.tags
}

module "lambda_rez_api_relay_prod" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.6.1"

  function_name = "lambda_rez_api_relay_prod"
  description   = "Lambda relay to rez-service api endpoint - prod"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"

  environment_variables = {
    request_url = "http://rez-service-internal-prod.dev.spinvfx.com/on-event"
    request_http_method = "POST"
  }

  source_path = "./lambda-relays/lambda-request-relay"

  vpc_subnet_ids         = local.eks_private_subnets_ids
  vpc_security_group_ids = local.eks_security_groups_ids
  attach_network_policy  = true

  tags = local.tags
}

module "lambda_scheduler_api_relay_dev" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.6.1"

  function_name = "lambda_scheduler_api_relay_dev"
  description   = "Lambda relay to scheduler-service api endpoint - dev"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"

  environment_variables = {
    request_url = "http://scheduler-internal.dev.spinvfx.com/on-event"
    request_http_method = "POST"
  }

  source_path = "./lambda-relays/lambda-request-relay"

  vpc_subnet_ids         = local.eks_private_subnets_ids
  vpc_security_group_ids = local.eks_security_groups_ids
  attach_network_policy  = true

  tags = local.tags
}

module "lambda_scheduler_job_api_relay_dev" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.6.1"

  function_name = "lambda_scheduler_job_api_relay_dev"
  description   = "Lambda relay to scheduler-service api endpoint - dev"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"

  environment_variables = {
    request_url = "http://scheduler-internal.dev.spinvfx.com/on-job-event"
    request_http_method = "POST"
  }

  source_path = "./lambda-relays/lambda-request-relay"

  vpc_subnet_ids         = local.eks_private_subnets_ids
  vpc_security_group_ids = local.eks_security_groups_ids
  attach_network_policy  = true

  tags = local.tags
}

module "lambda_scheduler_job_api_relay_uat" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.6.1"

  function_name = "lambda_scheduler_job_api_relay_uat"
  description   = "Lambda relay to scheduler-service api endpoint - uat"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"

  environment_variables = {
    request_url = "http://scheduler-internal-uat.dev.spinvfx.com/on-job-event"
    request_http_method = "POST"
  }

  source_path = "./lambda-relays/lambda-request-relay"

  vpc_subnet_ids         = local.eks_private_subnets_ids
  vpc_security_group_ids = local.eks_security_groups_ids
  attach_network_policy  = true

  tags = local.tags
}

module "lambda_scheduler_job_api_relay_prod" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.6.1"

  function_name = "lambda_scheduler_job_api_relay_prod"
  description   = "Lambda relay to scheduler-service api endpoint - prod"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"

  environment_variables = {
    request_url = "http://scheduler-internal-prod.dev.spinvfx.com/on-job-event"
    request_http_method = "POST"
  }

  source_path = "./lambda-relays/lambda-request-relay"

  vpc_subnet_ids         = local.eks_private_subnets_ids
  vpc_security_group_ids = local.eks_security_groups_ids
  attach_network_policy  = true

  tags = local.tags
}

module "lambda_scheduler_api_relay_uat" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.6.1"

  function_name = "lambda_scheduler_api_relay_uat"
  description   = "Lambda relay to scheduler-service api endpoint - uat"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"

  environment_variables = {
    request_url = "http://scheduler-internal-uat.dev.spinvfx.com/on-event"
    request_http_method = "POST"
  }

  source_path = "./lambda-relays/lambda-request-relay"

  vpc_subnet_ids         = local.eks_private_subnets_ids
  vpc_security_group_ids = local.eks_security_groups_ids
  attach_network_policy  = true

  tags = local.tags
}

module "lambda_scheduler_api_relay_prod" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.6.1"

  function_name = "lambda_scheduler_api_relay_prod"
  description   = "Lambda relay to scheduler-service api endpoint - prod"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"

  environment_variables = {
    request_url = "http://scheduler-internal-prod.dev.spinvfx.com/on-event"
    request_http_method = "POST"
  }

  source_path = "./lambda-relays/lambda-request-relay"

  vpc_subnet_ids         = local.eks_private_subnets_ids
  vpc_security_group_ids = local.eks_security_groups_ids
  attach_network_policy  = true

  tags = local.tags
}
