provider "aws" {
  region = "us-east-2" # Ohio
}

# 1. Red Básica
resource "aws_vpc" "retro_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "RetroCloud-PoC" }
}

resource "aws_subnet" "retro_subnet" {
  vpc_id                  = aws_vpc.retro_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "us-east-2a"
}

resource "aws_internet_gateway" "retro_igw" {
  vpc_id = aws_vpc.retro_vpc.id
}

resource "aws_route_table" "retro_rt" {
  vpc_id = aws_vpc.retro_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.retro_igw.id
  }
}

resource "aws_route_table_association" "retro_rta" {
  subnet_id      = aws_subnet.retro_subnet.id
  route_table_id = aws_route_table.retro_rt.id
}

# 2. Seguridad (RDP + DCV Web)
resource "aws_security_group" "builder_sg" {
  name        = "retro-builder-sg"
  vpc_id      = aws_vpc.retro_vpc.id

  ingress {
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # RDP para copiar archivos
  }
  
  ingress {
    from_port   = 8443
    to_port     = 8443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # DCV Web
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 3. La VM Builder (Manual)
resource "aws_instance" "builder_vm" {
  # Windows Server 2022 Base en Ohio
  ami           = "ami-0325e1499e14d1d8f" # Confirma si esta ID es correcta para Ohio, si no usa data source
  instance_type = "m7i-flex.large"
  key_name      = "keypairinfti"
  
  subnet_id              = aws_subnet.retro_subnet.id
  vpc_security_group_ids = [aws_security_group.builder_sg.id]

  # Disco suficiente para OS + ROMs
  root_block_device {
    volume_size = 50 
    volume_type = "gp3"
  }

  tags = {
    Name = "RetroCloud-Builder"
  }
}

output "builder_ip" {
  value = aws_instance.builder_vm.public_ip
}
