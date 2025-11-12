data "aws_ami" "win2022" {
  most_recent = true
  owners = ["801119661308"] # Amazon
  filter { name="name" values=["Windows_Server-2022-English-Full-Base-*"] }
}

resource "aws_security_group" "retro" {
  name   = "sg-retrocloud"
  vpc_id = aws_vpc.main.id
  ingress { from_port=80   to_port=80   protocol="tcp" cidr_blocks=["0.0.0.0/0"] }
  ingress { from_port=8443 to_port=8443 protocol="tcp" cidr_blocks=["0.0.0.0/0"] }
  # Opcional RDP solo desde tu IP:
  # ingress { from_port=3389 to_port=3389 protocol="tcp" cidr_blocks=["TU.IP.PUBLICA/32"] }
  egress  { from_port=0 to_port=0 protocol="-1" cidr_blocks=["0.0.0.0/0"] }
}

resource "aws_instance" "retro" {
  ami           = data.aws_ami.win2022.id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public1.id
  key_name      = var.key_name
  vpc_security_group_ids = [aws_security_group.retro.id]
  user_data = file("${path.module}/../scripts/windows_userdata.ps1")
  tags = { Name = "retrocloud-ec2", CodeDeploy = "yes" }
}

resource "aws_eip" "eip" {
  instance = aws_instance.retro.id
  domain   = "vpc"
}
