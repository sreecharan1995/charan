variable  "region" {
  type = string
  default = "us-east-1"
}

variable "lb_url_external" {
  type = string
  # default = "k8s-albgroupnew-ccc0708f3a-561773989.us-east-1.elb.amazonaws.com"
  default = "k8s-albspinvfxexterna-de4b9ea7ec-1158670129.us-east-1.elb.amazonaws.com"
}

variable "lb_url_internal" {
  type = string
  #default = "internal-k8s-albgroupnewintern-134df79c70-1123413053.us-east-1.elb.amazonaws.com"
  default = "internal-k8s-albspinvfxinterna-a2277aa81d-258923700.us-east-1.elb.amazonaws.com"
}

variable "allow_overwrite" {
  type = bool
  default = true
}
