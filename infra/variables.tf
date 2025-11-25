variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

variable "key_pair_name" {
  description = "Nombre de la keypair creada en AWS"
  type        = string
  default     = "keypairinfti" 
}

variable "project_name" {
  description = "Nombre base del proyecto"
  type        = string
  default     = "retrocloud"
}
