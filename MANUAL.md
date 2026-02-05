# Propositum-Fungorum
Интеллектуальная система, позволяющая проводить опрос, связанный с выбором хирургического лечения, на основе графовой модели принятия решений. Сами графы знаний извлекаются автоматически посредством использования LLM и имплементирования метода каскадных промптов.

## Установка и сборка
1. Необходимо склонировать репозиторий
```sh
# SSH
git clone git@github.com:nibbartemka/Propositum-Fungorum.git
# HTTPS
git clone https://github.com/nibbartemka/Propositum-Fungorum.git
```

2. Перейти в директорию проекта
```sh
cd ./Propositum-Fungorum
```

3. В корне проекта сформировать `.env` файл на основе `.env.example` 
```sh
cp .env.example .env
```

4. Подставить необходимые значения в ранее описанные `.env` вместо `***`
```sh
# MinIO root credentials (только для инициализации)
MINIO_ROOT_USER=***
MINIO_ROOT_PASSWORD=***

MINIO_APP_USER=***
MINIO_APP_PASSWORD=***

YANDEX_AUTH_TOKEN=***
YANDEX_MODEL_PACKAGE=***
```

Убедитесь, что у вас установлен и работает Docker
```sh
# Ссылка на скачивание Docker
https://www.docker.com/products/docker-desktop/
```
5. Находясь в корневой директории необходимо развернуть проект:
```sh
docker compose up -d --build
```

* Проект будет доступен на http://localhost/

* Загрузка своих клинических рекомендаций будет доступна на http://localhost/api/parser/docs

## 