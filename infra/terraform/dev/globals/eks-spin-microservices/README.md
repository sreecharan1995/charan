<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.1.9 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 4.13 |
| <a name="requirement_helm"></a> [helm](#requirement\_helm) | >= 2.4.1 |
| <a name="requirement_kubectl"></a> [kubectl](#requirement\_kubectl) | 1.14.0 |
| <a name="requirement_kubernetes"></a> [kubernetes](#requirement\_kubernetes) | >= 2.10 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | ~> 4.13 |
| <a name="provider_kubectl"></a> [kubectl](#provider\_kubectl) | 1.14.0 |
| <a name="provider_null"></a> [null](#provider\_null) | n/a |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_aws_vpc"></a> [aws\_vpc](#module\_aws\_vpc) | terraform-aws-modules/vpc/aws | ~> 3.0 |
| <a name="module_eks_blueprints"></a> [eks\_blueprints](#module\_eks\_blueprints) | github.com/aws-ia/terraform-aws-eks-blueprints | v4.17.0 |
| <a name="module_eks_blueprints_kubernetes_addons"></a> [eks\_blueprints\_kubernetes\_addons](#module\_eks\_blueprints\_kubernetes\_addons) | github.com/aws-ia/terraform-aws-eks-blueprints//modules/kubernetes-addons | v4.17.0 |
| <a name="module_lambda_dependency_api_relay"></a> [lambda\_dependency\_api\_relay](#module\_lambda\_dependency\_api\_relay) | terraform-aws-modules/lambda/aws | 4.6.1 |
| <a name="module_lambda_dependency_api_relay_prod"></a> [lambda\_dependency\_api\_relay\_prod](#module\_lambda\_dependency\_api\_relay\_prod) | terraform-aws-modules/lambda/aws | 4.6.1 |
| <a name="module_lambda_dependency_api_relay_uat"></a> [lambda\_dependency\_api\_relay\_uat](#module\_lambda\_dependency\_api\_relay\_uat) | terraform-aws-modules/lambda/aws | 4.6.1 |
| <a name="module_lambda_rez_api_relay"></a> [lambda\_rez\_api\_relay](#module\_lambda\_rez\_api\_relay) | terraform-aws-modules/lambda/aws | 4.6.1 |
| <a name="module_lambda_rez_api_relay_prod"></a> [lambda\_rez\_api\_relay\_prod](#module\_lambda\_rez\_api\_relay\_prod) | terraform-aws-modules/lambda/aws | 4.6.1 |
| <a name="module_lambda_rez_api_relay_uat"></a> [lambda\_rez\_api\_relay\_uat](#module\_lambda\_rez\_api\_relay\_uat) | terraform-aws-modules/lambda/aws | 4.6.1 |
| <a name="module_terraform_state_backend"></a> [terraform\_state\_backend](#module\_terraform\_state\_backend) | cloudposse/tfstate-backend/aws | 0.38.1 |

## Resources

| Name | Type |
|------|------|
| [aws_iam_policy.dev-role-developer_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_role.kubectl_dev_user-assume-dev-role-developer](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_user.kubectl_dev_user](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_user) | resource |
| [aws_iam_user_policy_attachment.kubectl_dev_user-policy_attachment](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_user_policy_attachment) | resource |
| [kubectl_manifest.inject_Ingress](https://registry.terraform.io/providers/gavinbunney/kubectl/1.14.0/docs/resources/manifest) | resource |
| [kubectl_manifest.inject_Ingress_internal](https://registry.terraform.io/providers/gavinbunney/kubectl/1.14.0/docs/resources/manifest) | resource |
| [kubectl_manifest.inject_RBAC](https://registry.terraform.io/providers/gavinbunney/kubectl/1.14.0/docs/resources/manifest) | resource |
| [kubectl_manifest.inject_datashin](https://registry.terraform.io/providers/gavinbunney/kubectl/1.14.0/docs/resources/manifest) | resource |
| [kubectl_manifest.inject_namespaces](https://registry.terraform.io/providers/gavinbunney/kubectl/1.14.0/docs/resources/manifest) | resource |
| [null_resource.create_s3_configurations](https://registry.terraform.io/providers/hashicorp/null/latest/docs/resources/resource) | resource |
| [null_resource.create_s3_levels_tree](https://registry.terraform.io/providers/hashicorp/null/latest/docs/resources/resource) | resource |
| [null_resource.create_s3_permission_matrix](https://registry.terraform.io/providers/hashicorp/null/latest/docs/resources/resource) | resource |
| [null_resource.create_s3_rez_uat](https://registry.terraform.io/providers/hashicorp/null/latest/docs/resources/resource) | resource |
| [aws_availability_zones.available](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/availability_zones) | data source |
| [kubectl_file_documents.datashim_manifest](https://registry.terraform.io/providers/gavinbunney/kubectl/1.14.0/docs/data-sources/file_documents) | data source |
| [kubectl_filename_list.Ingress_files](https://registry.terraform.io/providers/gavinbunney/kubectl/1.14.0/docs/data-sources/filename_list) | data source |
| [kubectl_filename_list.Ingress_internal_files](https://registry.terraform.io/providers/gavinbunney/kubectl/1.14.0/docs/data-sources/filename_list) | data source |
| [kubectl_filename_list.Namespaces_files](https://registry.terraform.io/providers/gavinbunney/kubectl/1.14.0/docs/data-sources/filename_list) | data source |
| [kubectl_filename_list.RBAC_files](https://registry.terraform.io/providers/gavinbunney/kubectl/1.14.0/docs/data-sources/filename_list) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_enable_spot_asg"></a> [enable\_spot\_asg](#input\_enable\_spot\_asg) | n/a | `bool` | `false` | no |
| <a name="input_environment"></a> [environment](#input\_environment) | Environment area, e.g. prod or preprod | `string` | `"dev"` | no |
| <a name="input_region"></a> [region](#input\_region) | n/a | `string` | `"us-east-1"` | no |
| <a name="input_tenant"></a> [tenant](#input\_tenant) | Account Name or unique account unique id e.g., apps or management or aws007 | `string` | `"spinvfx"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_configure_kubectl"></a> [configure\_kubectl](#output\_configure\_kubectl) | Configure kubectl: make sure you're logged in with the correct AWS profile and run the following command to update your kubeconfig |
| <a name="output_eks_cluster_id"></a> [eks\_cluster\_id](#output\_eks\_cluster\_id) | EKS cluster ID |
| <a name="output_eks_managed_node_group_aws_auth_config_map"></a> [eks\_managed\_node\_group\_aws\_auth\_config\_map](#output\_eks\_managed\_node\_group\_aws\_auth\_config\_map) | EKS managed node group status |
| <a name="output_eks_managed_nodegroup_arns"></a> [eks\_managed\_nodegroup\_arns](#output\_eks\_managed\_nodegroup\_arns) | EKS managed node group arns |
| <a name="output_eks_managed_nodegroup_ids"></a> [eks\_managed\_nodegroup\_ids](#output\_eks\_managed\_nodegroup\_ids) | EKS managed node group ids |
| <a name="output_eks_managed_nodegroup_role_name"></a> [eks\_managed\_nodegroup\_role\_name](#output\_eks\_managed\_nodegroup\_role\_name) | EKS managed node group role name |
| <a name="output_eks_managed_nodegroup_status"></a> [eks\_managed\_nodegroup\_status](#output\_eks\_managed\_nodegroup\_status) | EKS managed node group status |
| <a name="output_eks_managed_nodegroups"></a> [eks\_managed\_nodegroups](#output\_eks\_managed\_nodegroups) | EKS managed node groups |
| <a name="output_nat_public_ips"></a> [nat\_public\_ips](#output\_nat\_public\_ips) | List of public Elastic IPs created for AWS NAT Gateway |
| <a name="output_region"></a> [region](#output\_region) | AWS region |
| <a name="output_vpc_cidr"></a> [vpc\_cidr](#output\_vpc\_cidr) | VPC CIDR |
| <a name="output_vpc_private_subnet_cidr"></a> [vpc\_private\_subnet\_cidr](#output\_vpc\_private\_subnet\_cidr) | VPC private subnet CIDR |
| <a name="output_vpc_public_subnet_cidr"></a> [vpc\_public\_subnet\_cidr](#output\_vpc\_public\_subnet\_cidr) | VPC public subnet CIDR |
<!-- END_TF_DOCS -->