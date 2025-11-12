resource "aws_codedeploy_app" "app" {
  name = "retrocloud-app"
  compute_platform = "Server"
}

# El Service Role (CodeDeployServiceRole) debe ser creado manualmente en IAM con los permisos para desplegar.
# AWS niega todos los permisos a menos qeu explícitamente le digas lo contrario.
resource "aws_codedeploy_deployment_group" "dg" {
  app_name              = aws_codedeploy_app.app.name
  deployment_group_name = "retrocloud-dg"
  service_role_arn      = "arn:aws:iam::276553701880:role/CodeDeployServiceRole"
  deployment_style { deployment_option = "WITH_TRAFFIC_CONTROL" deployment_type="IN_PLACE" }
  ec2_tag_set {
    ec2_tag_filter { key="Name" type="KEY_AND_VALUE" value="retrocloud-ec2" }
  }
  load_balancer_info {}
}
