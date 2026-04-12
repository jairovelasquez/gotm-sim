variable "region" {
  description = "AWS Region"
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  default     = "t3.medium"
}

variable "volume_size" {
  description = "Root volume size in GB"
  default     = 30
}

variable "project_name" {
  default = "gotm-sim"
}
