<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.1.9 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 4.13 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | ~> 4.13 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_route53_record._c4a5dd9a4108978079f6803d72244af7_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.configs-internal-prod_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.configs-internal-uat_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.configs-internal_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.configs-prod_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.configs-uat_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.configs_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.dashboard-prod_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.dashboard-uat_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.dashboard_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.dependencies-internal_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.dependencies-internal_prod_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.dependencies-internal_uat_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.dependencies-prod_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.dependencies-uat_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.dependencies_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.dev_spinvfx_com_NS_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.dev_spinvfx_com_SOA_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.levels-internal-prod_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.levels-internal-uat_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.levels-internal_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.levels-prod_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.levels-uat_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.levels_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.rez-service-internal-prod_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.rez-service-internal-uat_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.rez-service-internal_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.rez-service-prod_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.rez-service-uat_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.rez-service_dev_spinvfx_com_CNAME_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_zone.dev_spinvfx_com_zone](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_zone) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_allow_overwrite"></a> [allow\_overwrite](#input\_allow\_overwrite) | n/a | `bool` | `true` | no |
| <a name="input_lb_url_external"></a> [lb\_url\_external](#input\_lb\_url\_external) | n/a | `string` | `"k8s-albspinvfxexterna-de4b9ea7ec-1158670129.us-east-1.elb.amazonaws.com"` | no |
| <a name="input_lb_url_internal"></a> [lb\_url\_internal](#input\_lb\_url\_internal) | n/a | `string` | `"internal-k8s-albspinvfxinterna-a2277aa81d-258923700.us-east-1.elb.amazonaws.com"` | no |
| <a name="input_region"></a> [region](#input\_region) | n/a | `string` | `"us-east-1"` | no |

## Outputs

No outputs.
<!-- END_TF_DOCS -->