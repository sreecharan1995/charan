output "spinvfx_id" {
  description = "Spinvfx ID"
  value       = "${data.aws_vpc.spinvfx-net.id}"
}

output "eks_private_subnets_ids" {
  description = "eks private subnets id"
  value       = "${data.aws_subnets.eks-private-subnets-ids.ids}"
}

output "eks-spinvfx-security-groups_id" {
  description = ""
  value       = "${data.aws_security_groups.eks-spinvfx-security-groups.ids}"
}
