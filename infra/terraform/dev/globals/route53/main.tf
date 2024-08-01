####################################################################################################################
# terraform state module                                                                                           #
# https://registry.terraform.io/modules/cloudposse/tfstate-backend/aws/latest                                      #
####################################################################################################################
module "terraform_state_backend" {
  source     = "cloudposse/tfstate-backend/aws"
  version    = "0.38.1"
  namespace  = "spinfx"
  stage      = "dev"
  name       = "route53e"
  attributes = ["state"]

  terraform_backend_config_file_path = "."
  terraform_backend_config_file_name = "backend.tf"
  force_destroy                      = false

  terraform_version = "1.1.9"
}

####################################################################################################################
# dev.spinvfx.com zone records                                                                                     #
####################################################################################################################
resource "aws_route53_zone" "dev_spinvfx_com_zone" {
  comment       = "All services running in the dev environment of the spin microservices projects"
  force_destroy = "false"
  name          = "dev.spinvfx.com"
}

resource "aws_route53_record" "dev_spinvfx_com_NS_record" {
  name    = "dev.spinvfx.com"
  records = ["ns-1286.awsdns-32.org.", "ns-1591.awsdns-06.co.uk.", "ns-444.awsdns-55.com.", "ns-924.awsdns-51.net."]
  ttl     = "172800"
  type    = "NS"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
}

resource "aws_route53_record" "dev_spinvfx_com_SOA_record" {
  name    = "dev.spinvfx.com"
  records = ["ns-924.awsdns-51.net. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400"]
  ttl     = "900"
  type    = "SOA"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
}

resource "aws_route53_record" "_c4a5dd9a4108978079f6803d72244af7_dev_spinvfx_com_CNAME_record" {
  name    = "_c4a5dd9a4108978079f6803d72244af7.dev.spinvfx.com"
  records = ["_c56a7c6bd3eec7ff4f22367e8cb96ada.mqzgcdqkwq.acm-validations.aws."]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
}

# local var declarations

locals {

  allow_overwrite = var.allow_overwrite

}

# config service

resource "aws_route53_record" "configs_dev_spinvfx_com_CNAME_record" {
  name    = "configs.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "configs-uat_dev_spinvfx_com_CNAME_record" {
  name    = "configs-uat.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "configs-prod_dev_spinvfx_com_CNAME_record" {
  name    = "configs-prod.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "configs-internal_dev_spinvfx_com_CNAME_record" {
  name    = "configs-internal.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "configs-internal-uat_dev_spinvfx_com_CNAME_record" {
  name    = "configs-internal-uat.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "configs-internal-prod_dev_spinvfx_com_CNAME_record" {
  name    = "configs-internal-prod.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

# portal

resource "aws_route53_record" "dashboard_dev_spinvfx_com_CNAME_record" {
  name    = "dashboard.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "dashboard-uat_dev_spinvfx_com_CNAME_record" {
  name    = "dashboard-uat.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "dashboard-prod_dev_spinvfx_com_CNAME_record" {
  name    = "dashboard-prod.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

# dependency service

resource "aws_route53_record" "dependencies_dev_spinvfx_com_CNAME_record" {
  name    = "dependencies.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "dependencies-uat_dev_spinvfx_com_CNAME_record" {
  name    = "dependencies-uat.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "dependencies-prod_dev_spinvfx_com_CNAME_record" {
  name    = "dependencies-prod.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "dependencies-internal_dev_spinvfx_com_CNAME_record" {
  name    = "dependencies-internal.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "dependencies-internal_uat_spinvfx_com_CNAME_record" {
  name    = "dependencies-internal-uat.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "dependencies-internal_prod_spinvfx_com_CNAME_record" {
  name    = "dependencies-internal-prod.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

# levels service

resource "aws_route53_record" "levels_dev_spinvfx_com_CNAME_record" {
  name    = "levels.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "levels-uat_dev_spinvfx_com_CNAME_record" {
  name    = "levels-uat.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "levels-prod_dev_spinvfx_com_CNAME_record" {
  name    = "levels-prod.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "levels-internal_dev_spinvfx_com_CNAME_record" {
  name    = "levels-internal.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "levels-internal-uat_dev_spinvfx_com_CNAME_record" {
  name    = "levels-internal-uat.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "levels-internal-prod_dev_spinvfx_com_CNAME_record" {
  name    = "levels-internal-prod.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

# rez-service

resource "aws_route53_record" "rez-service_dev_spinvfx_com_CNAME_record" {
  name    = "rez-service.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "rez-service-uat_dev_spinvfx_com_CNAME_record" {
  name    = "rez-service-uat.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "rez-service-prod_dev_spinvfx_com_CNAME_record" {
  name    = "rez-service-prod.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "rez-service-internal_dev_spinvfx_com_CNAME_record" {
  name    = "rez-service-internal.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "rez-service-internal-uat_dev_spinvfx_com_CNAME_record" {
  name    = "rez-service-internal-uat.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "rez-service-internal-prod_dev_spinvfx_com_CNAME_record" {
  name    = "rez-service-internal-prod.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

# sourcing service

resource "aws_route53_record" "sourcing_dev_spinvfx_com_CNAME_record" {
  name    = "sourcing.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "sourcing-uat_dev_spinvfx_com_CNAME_record" {
  name    = "sourcing-uat.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "sourcing-prod_dev_spinvfx_com_CNAME_record" {
  name    = "sourcing-prod.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "sourcing-internal_dev_spinvfx_com_CNAME_record" {
  name    = "sourcing-internal.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "sourcing-internal-uat_dev_spinvfx_com_CNAME_record" {
  name    = "sourcing-internal-uat.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "sourcing-internal-prod_dev_spinvfx_com_CNAME_record" {
  name    = "sourcing-internal-prod.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

# scheduling service

resource "aws_route53_record" "scheduling-internal_dev_spinvfx_com_CNAME_record" {
  name    = "scheduler-internal.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "scheduling-internal-uat_dev_spinvfx_com_CNAME_record" {
  name    = "scheduler-internal-uat.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "scheduling-internal-prod_dev_spinvfx_com_CNAME_record" {
  name    = "scheduler-internal-prod.dev.spinvfx.com"
  records = [var.lb_url_internal]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "scheduler_dev_spinvfx_com_CNAME_record" {
  name    = "scheduler.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "scheduler-uat_dev_spinvfx_com_CNAME_record" {
  name    = "scheduler-uat.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}

resource "aws_route53_record" "scheduler-internal-prod_dev_spinvfx_com_CNAME_record" {
  name    = "scheduler-prod.dev.spinvfx.com"
  records = [var.lb_url_external]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "${aws_route53_zone.dev_spinvfx_com_zone.zone_id}"
  allow_overwrite = local.allow_overwrite
}
