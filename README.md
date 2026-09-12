# AtomicHabits

REST API для трекинга полезных привычек с напоминаниями в Telegram.
Проект контейнеризирован, автоматически тестируется и деплоится через GitHub Actions.

## Стек:
* Backend
* Аутентификация 
* База данных 
* Брокер / кэш 
* Фоновые задачи 
* Веб-сервер 
* Reverse proxy 
* Контейнеризация 
* CI/CD |
* Реестр образов 


Все сервисы запускаются одной командой `docker compose up` и общаются внутри общей
Docker-сети по именам сервисов (`db`, `redis`, `web`).

## Локальный запуск

### Требования

- Docker 24+
- Docker Compose v2
- Git

### Шаги

1. Клонировать репозиторий:

   git clone git@github.com:RomanZ737/AtomicHabits.git
   cd AtomicHabits

2. Создать .env на основе примера

   cp .env.sample .env

3. Заполнить .env

4. Собрать и запустить:
   docker compose up --build -d

5. Применить миграции и создать суперпользователя:
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser

6. Приложение доступно по адресу http://localhost/:
    API: http://localhost/api/
    Swagger: http://localhost/swagger/
    Админка: http://localhost/admin/
7. Остановка:
    docker compose down          # остановить
    docker compose down -v       # остановить и удалить volumes

### Переменные окружения:
Все переменные хранятся в .env
Шаблон — .env.sample.

* SECRET_KEY	Секретный ключ Django	django-insecure-...
* DEBUG	Режим отладки	False
* ALLOWED_HOSTS	Разрешённые хосты через запятую	1.2.3.4,localhost,127.0.0.1
* CSRF_TRUSTED_ORIGINS	Доверенные origin-ы для CSRF	http://1.2.3.4
* CORS_ALLOWED_ORIGINS	Разрешённые CORS-origin-ы	http://1.2.3.4
* POSTGRES_DB	Имя базы данных	atomic_habits
* POSTGRES_USER	Пользователь БД	atomic_user
* POSTGRES_PASSWORD	Пароль БД	strong_password
* POSTGRES_HOST	Хост БД (в compose — имя сервиса)	db
* POSTGRES_PORT	Порт БД	5432
* CELERY_BROKER_URL	URL брокера Celery	redis://redis:6379/0
* CELERY_RESULT_BACKEND	URL backend результатов	redis://redis:6379/0
* TELEGRAM_BOT_TOKEN	Токен Telegram-бота	123456:ABC-DEF...
* DOCKER_HUB_USERNAME	Логин Docker Hub	roman737
* DOCKER_IMAGE_TAG	Тег образа	latest

### CI/CD
Пайплайн описан в .github/workflows/ci.yml и запускается при пуше в main

* lint	Устанавливает flake8 и проверяет стиль кода
* test	Поднимает Postgres и Redis как service-контейнеры, ставит зависимости, применяет миграции и запускает python manage.py test
* build	Собирает Docker-образ и пушит в Docker Hub под тегами :latest и :<git-sha>
* deploy	По SSH заходит на сервер, логинится в Docker Hub, обновляет docker-compose.yml и nginx.conf, подтягивает образ и поднимает контейнеры

### Секреты GitHub Actions
* SECRET_KEY	Django SECRET_KEY для продакшена
* DOCKER_HUB_USERNAME	Логин Docker Hub (только строчные буквы!)
* DOCKER_HUB_ACCESS_TOKEN	Access Token из Docker Hub (Settings → Security)
* SERVER_IP	Публичный IP сервера
* SSH_USER	Имя SSH-пользователя для деплоя
* SSH_KEY	Приватный SSH-ключ (целиком, с BEGIN/END)
* DEPLOY_DIR	Абсолютный путь на сервере, например /var/www/AtomicHabits


**Настройка сервера**

1. Установка Docker и Docker Compose
    sudo apt update
    sudo apt install -y ca-certificates curl gnupg
    curl -fsSL https://get.docker.com | sudo sh
    sudo apt install -y docker-compose-plugin
    
    # Добавить текущего пользователя в группу docker
    sudo usermod -aG docker $USER
    newgrp docker

2. Создание директории для деплоя
   sudo mkdir -p /var/www/AtomicHabits
   sudo chown $USER:$USER /var/www/AtomicHabits

3. Создание .env на сервере
   cd /var/www/AtomicHabits
   nano .env
   ### Заполнить по шаблону .env.sample, обязательно:
    POSTGRES_HOST=
    CELERY_BROKER_URL=
    CELERY_RESULT_BACKEND=
    ALLOWED_HOSTS=<IP_сервера>,localhost,127.0.0.1
    CSRF_TRUSTED_ORIGINS=
    DEBUG=False
    DOCKER_HUB_USERNAME=

4. Первый деплой
   Запушить в main:
    git push origin main