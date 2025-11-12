resource "aws_dynamodb_table" "users" {
  name         = "retro_users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "username"
  attribute { name="username" type="S" }
}

resource "aws_dynamodb_table" "sessions" {
  name         = "retro_sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "username"
  attribute { name="username" type="S" }
  ttl { attribute_name = "expires_at" enabled = true }
}
