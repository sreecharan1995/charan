<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.1.9 |
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.1.9 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 4.13 |

## Providers

No providers.

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_configs-configurations-dev"></a> [configs-configurations-dev](#module\_configs-configurations-dev) | terraform-aws-modules/s3-bucket/aws | 3.4.0 |
| <a name="module_configs-configurations-prod"></a> [configs-configurations-prod](#module\_configs-configurations-prod) | terraform-aws-modules/s3-bucket/aws | 3.4.0 |
| <a name="module_configs-configurations-uat"></a> [configs-configurations-uat](#module\_configs-configurations-uat) | terraform-aws-modules/s3-bucket/aws | 3.4.0 |
| <a name="module_levels-tree-prod"></a> [levels-tree-prod](#module\_levels-tree-prod) | terraform-aws-modules/s3-bucket/aws | 3.4.0 |
| <a name="module_levels-tree-uat"></a> [levels-tree-uat](#module\_levels-tree-uat) | terraform-aws-modules/s3-bucket/aws | 3.4.0 |
| <a name="module_permission-matrix-prod"></a> [permission-matrix-prod](#module\_permission-matrix-prod) | terraform-aws-modules/s3-bucket/aws | 3.4.0 |
| <a name="module_permission-matrix-uat"></a> [permission-matrix-uat](#module\_permission-matrix-uat) | terraform-aws-modules/s3-bucket/aws | 3.4.0 |
| <a name="module_s3"></a> [s3](#module\_s3) | terraform-aws-modules/s3-bucket/aws | 3.4.0 |
| <a name="module_spin-rez-prod"></a> [spin-rez-prod](#module\_spin-rez-prod) | terraform-aws-modules/s3-bucket/aws | 3.4.0 |
| <a name="module_terraform_state_backend"></a> [terraform\_state\_backend](#module\_terraform\_state\_backend) | cloudposse/tfstate-backend/aws | 0.38.1 |

## Resources

No resources.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_region"></a> [region](#input\_region) | n/a | `string` | `"us-east-1"` | no |

## Outputs

No outputs.
<!-- END_TF_DOCS -->