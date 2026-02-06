#!/bin/sh

echo "⏳ Waiting for MinIO..."

until mc alias set "$MINIO_ALIAS" "$MINIO_ENDPOINT" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" 2>/dev/null; do
  sleep 2
done

echo "✅ MinIO is available"

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

# === Создаём пользователя для приложения ===
echo "🔐 Creating application user..."

# Проверяем, существует ли пользователь
if ! mc admin user info "$MINIO_ALIAS" "$MINIO_APP_USER" > /dev/null 2>&1; then
  mc admin user add "$MINIO_ALIAS" "$MINIO_APP_USER" "$MINIO_APP_PASSWORD"
  echo "✅ User '$MINIO_APP_USER' created"
else
  echo "ℹ️ User '$MINIO_APP_USER' already exists"
fi


# Применяем политику
mc admin policy attach "$MINIO_ALIAS" readwrite --user "$MINIO_APP_USER"

echo "🎉 MinIO buckets and application user initialized"
echo "🔑 Application credentials:"
echo "   Access Key: $MINIO_APP_USER"
echo "   Secret Key: $MINIO_APP_PASSWORD"

