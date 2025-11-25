resource "aws_instance" "retrocloud_game_builder" {
  ami                    = data.aws_ami.ubuntu.id   # o la AMI de Windows si vas con Windows
  instance_type          = "m7i-flex.large"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.main_sg.id]
  key_name               = var.key_pair_name

  tags = {
    Name = "${var.project_name}-game-builder"
  }
}
