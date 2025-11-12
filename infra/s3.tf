resource "aws_s3_bucket" "artifacts" {
  bucket = var.artifact_bucket
  force_destroy = true
}

resource "aws_s3_bucket" "roms" {
  bucket = var.roms_bucket
}

resource "aws_s3_bucket" "roms_replica" {
  provider = aws
  bucket   = var.roms_replica_bucket
  # Para demo: sin versioning + replication policy completa (agregable luego)
}

resource "aws_s3_bucket_versioning" "roms_v" {
  bucket = aws_s3_bucket.roms.id
  versioning_configuration { status = "Enabled" }
}
# La replicación completa requiere role/policy; por brevedad la omito aquí,
# pero la config estándar es: aws_s3_bucket_replication_configuration.
