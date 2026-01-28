#!/bin/sh
set -e

echo "⏳ Waiting for MinIO..."

until mc alias set "$MINIO_ALIAS" "$MINIO_ENDPOINT" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" 2>/dev/null; do
  sleep 2
done

echo "✅ MinIO is available"

# Перебираем переменные окружения вручную
for entry in $(env); do
  case "$entry" in
    BUCKET_[0-9]=*)
      key="${entry%%=*}"
      bucket="${entry#*=}"

      echo "📦 Creating bucket: $bucket"
      mc mb "$MINIO_ALIAS/$bucket" --ignore-existing

      index="${key#BUCKET_}"

      public_var="BUCKET_PUBLIC_${index}"
      versioning_var="BUCKET_VERSIONING_${index}"

      eval public_val=\$$public_var
      eval versioning_val=\$$versioning_var

      if [ "$public_val" = "true" ]; then
        echo "🌍 Setting public access for $bucket"
        mc anonymous set download "$MINIO_ALIAS/$bucket"
      fi

      if [ "$versioning_val" = "true" ]; then
        echo "🕘 Enabling versioning for $bucket"
        mc version enable "$MINIO_ALIAS/$bucket"
      fi
      ;;
  esac
done

echo "🎉 MinIO buckets initialized"
