<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.1.9 |
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.1.9 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 4.13 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | ~> 4.13 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_eventbridge"></a> [eventbridge](#module\_eventbridge) | terraform-aws-modules/eventbridge/aws | 1.14.0 |
| <a name="module_eventbridge_prod"></a> [eventbridge\_prod](#module\_eventbridge\_prod) | terraform-aws-modules/eventbridge/aws | 1.14.0 |
| <a name="module_eventbridge_uat"></a> [eventbridge\_uat](#module\_eventbridge\_uat) | terraform-aws-modules/eventbridge/aws | 1.14.0 |
| <a name="module_terraform_state_backend"></a> [terraform\_state\_backend](#module\_terraform\_state\_backend) | cloudposse/tfstate-backend/aws | 0.38.1 |

## Resources

| Name | Type |
|------|------|
| [aws_cloudwatch_log_group.dev_bus_cloudwatch_logs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_cloudwatch_log_group.prod_bus_cloudwatch_logs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_cloudwatch_log_group.uat_bus_cloudwatch_logs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_lambda_permission.lambda_dependency_api_relay_invoke](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_lambda_permission.lambda_dependency_api_relay_prod_invoke](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_lambda_permission.lambda_dependency_api_relay_uat_invoke](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_lambda_permission.lambda_rez_api_relay_invoke](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_lambda_permission.lambda_rez_api_relay_prod_invoke](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_lambda_permission.lambda_rez_api_relay_uat_invoke](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_dev_bus_name"></a> [dev\_bus\_name](#input\_dev\_bus\_name) | n/a | `string` | `"dev-bus"` | no |
| <a name="input_prod_bus_name"></a> [prod\_bus\_name](#input\_prod\_bus\_name) | n/a | `string` | `"prod-bus"` | no |
| <a name="input_region"></a> [region](#input\_region) | n/a | `string` | `"us-east-1"` | no |
| <a name="input_uat_bus_name"></a> [uat\_bus\_name](#input\_uat\_bus\_name) | n/a | `string` | `"uat-bus"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_eventbridge_api_destination_arns"></a> [eventbridge\_api\_destination\_arns](#output\_eventbridge\_api\_destination\_arns) | The EventBridge API Destination ARNs |
| <a name="output_eventbridge_bus_arn"></a> [eventbridge\_bus\_arn](#output\_eventbridge\_bus\_arn) | The EventBridge Bus ARN |
| <a name="output_eventbridge_connection_arns"></a> [eventbridge\_connection\_arns](#output\_eventbridge\_connection\_arns) | The EventBridge Connection ARNs |
| <a name="output_eventbridge_connection_ids"></a> [eventbridge\_connection\_ids](#output\_eventbridge\_connection\_ids) | The EventBridge Connection IDs created |
<!-- END_TF_DOCS -->