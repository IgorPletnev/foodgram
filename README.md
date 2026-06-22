<div align="center">
  <h1>🍳 Foodgram</h1>
  <p><strong>Продуктовый помощник — сервис для публикации рецептов</strong></p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python" alt="Python">
    <img src="https://img.shields.io/badge/Django-5.1.1-092E20?logo=django" alt="Django">
    <img src="https://img.shields.io/badge/DRF-3.15.2-red?logo=django" alt="DRF">
    <img src="https://img.shields.io/badge/React-18-blue?logo=react" alt="React">
    <img src="https://img.shields.io/badge/PostgreSQL-13-336791?logo=postgresql" alt="PostgreSQL">
    <img src="https://img.shields.io/badge/Docker-✓-2496ED?logo=docker" alt="Docker">
    <img src="https://img.shields.io/badge/Nginx-1.25-009639?logo=nginx" alt="Nginx">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </p>
  <p>
    <strong>🔗 Проект в продакшене:</strong>
    <a href="https://julik.ddns.net">https://julik.ddns.net</a>
  </p>
</div>

---

## 📋 О проекте

**Foodgram** — это веб-приложение, где пользователи могут:

- 📝 **Публиковать рецепты** с подробным описанием, ингредиентами, тегами и изображениями
- ❤️ **Добавлять рецепты в избранное**
- 🛒 **Формировать список покупок** — скачать его в формате TXT
- 👤 **Подписываться на авторов**
- 🔗 **Делиться рецептами** по короткой ссылке
- 🖼️ **Загружать аватар**

Проект полностью контейнеризирован и готов к развёртыванию на сервере.

---

## 🚀 Быстрый старт (локальная разработка)

### Требования

- [Docker](https://docs.docker.com/get-docker/) 24+
- [Docker Compose](https://docs.docker.com/compose/install/) 2.20+

### Запуск

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/IgorPletnev/foodgram.git
cd foodgram

# 2. Создайте файл окружения
cp infra/.env.example infra/.env
# Отредактируйте infra/.env под свои нужды

# 3. Запустите контейнеры
cd infra
docker compose up -d --build
```

После запуска:

| Сервис | Адрес |
|--------|-------|
| 🌐 **Сайт** | http://localhost:8000 |
| 🔌 **API** | http://localhost:8000/api/ |
| 📖 **Документация API** | `docs/openapi-schema.yml` |

### Полезные команды

```bash
# Загрузить ингредиенты в БД
docker compose exec backend python manage.py load_ingredients

# Создать суперпользователя
docker compose exec backend python manage.py createsuperuser

# Посмотреть логи
docker compose logs -f backend

# Остановить все контейнеры
docker compose down
```

---

## 🏗️ Архитектура

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Browser   │────▶│    Nginx     │────▶│    Django    │
│ localhost:8000│    │  :80 → :8000 │    │  Gunicorn    │
└─────────────┘     └──────┬───────┘     └──────┬───────┘
                           │                    │
                           │              ┌─────▼──────┐
                           │              │ PostgreSQL │
                           │              └────────────┘
                     ┌─────▼───────┐
                     │   React     │
                     │  Frontend   │
                     └─────────────┘
```

### Стек технологий

| Компонент | Технология |
|-----------|-----------|
| **Backend** | Django 5.1.1, Django REST Framework 3.15.2 |
| **Frontend** | React 18 |
| **База данных** | PostgreSQL 13 |
| **Веб-сервер** | Nginx 1.25 (reverse proxy) |
| **WSGI-сервер** | Gunicorn |
| **Контейнеризация** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |
| **Аутентификация** | Djoser 2.3.1 (Token-based) |
| **Фильтрация** | django-filter 24.3 |

---

## 📡 API Эндпоинты

### Пользователи

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `POST` | `/api/users/` | Регистрация нового пользователя |
| `GET` | `/api/users/{id}/` | Профиль пользователя |
| `GET` | `/api/users/me/` | Текущий пользователь |
| `PUT` | `/api/users/me/avatar/` | Загрузить/обновить аватар |
| `DELETE` | `/api/users/me/avatar/` | Удалить аватар |
| `POST` | `/api/users/set_password/` | Сменить пароль |

### Аутентификация

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `POST` | `/api/auth/token/login/` | Вход (получить токен) |
| `POST` | `/api/auth/token/logout/` | Выход (удалить токен) |

### Подписки

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/api/users/subscriptions/` | Мои подписки |
| `POST` | `/api/users/{id}/subscribe/` | Подписаться |
| `DELETE` | `/api/users/{id}/subscribe/` | Отписаться |

### Рецепты

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/api/recipes/` | Список рецептов (с фильтрацией) |
| `POST` | `/api/recipes/` | Создать рецепт |
| `GET` | `/api/recipes/{id}/` | Детали рецепта |
| `PATCH` | `/api/recipes/{id}/` | Частичное обновление |
| `DELETE` | `/api/recipes/{id}/` | Удалить рецепт |
| `POST` | `/api/recipes/{id}/favorite/` | Добавить в избранное |
| `DELETE` | `/api/recipes/{id}/favorite/` | Удалить из избранного |
| `POST` | `/api/recipes/{id}/shopping_cart/` | Добавить в корзину |
| `DELETE` | `/api/recipes/{id}/shopping_cart/` | Удалить из корзины |
| `GET` | `/api/recipes/{id}/get-link/` | Получить короткую ссылку |
| `GET` | `/api/recipes/download_shopping_cart/` | Скачать список покупок |

### Теги и ингредиенты

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/api/tags/` | Список тегов |
| `GET` | `/api/ingredients/` | Список ингредиентов (с поиском по `?name=`) |

### Фильтрация рецептов

| Параметр | Пример | Описание |
|----------|--------|----------|
| `author` | `?author=1` | Фильтр по ID автора |
| `tags` | `?tags=breakfast&tags=lunch` | Фильтр по слагам тегов |
| `is_favorited` | `?is_favorited=1` | Только в избранном |
| `is_in_shopping_cart` | `?is_in_shopping_cart=1` | Только в корзине |

### Пагинация

| Параметр | Пример | Описание |
|----------|--------|----------|
| `page` | `?page=2` | Номер страницы |
| `limit` | `?limit=10` | Количество записей на странице (по умолчанию: 6) |

---

## 📁 Структура проекта

```
foodgram/
├── backend/                    # Django-приложение
│   ├── api/                    # API (views, serializers, filters)
│   ├── foodgram/               # Конфигурация Django
│   ├── recipes/                # Модели рецептов
│   ├── users/                  # Модели пользователей
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # React-приложение
│   ├── src/
│   └── Dockerfile
├── infra/                      # Инфраструктура
│   ├── docker-compose.yml      # Локальная разработка (сборка из исходников)
│   ├── docker-compose.prod.yml # Продакшен (образы с Docker Hub)
│   ├── nginx.conf
│   └── .env.example
├── docs/                       # Документация
│   └── openapi-schema.yml
├── data/                       # Данные для загрузки
│   └── ingredients.json
├── postman_collection/         # Postman-тесты
│   └── foodgram.postman_collection.json
└── .github/workflows/          # CI/CD
    └── deploy.yml
```

---

## ⚙️ Переменные окружения

Создайте файл `infra/.env` (скопируйте из `infra/.env.example`):

```env
# PostgreSQL
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=your_strong_password_here
DB_HOST=db
DB_PORT=5432

# Django
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost 127.0.0.1 81.26.184.67 julik.ddns.net
CSRF_TRUSTED_ORIGINS=http://localhost:8000 http://81.26.184.67 https://julik.ddns.net

# Frontend URL (для short-link редиректа)
FRONTEND_URL=https://julik.ddns.net
```

---

## 🌐 Деплой на сервер

### Подготовка сервера

На сервере должны быть установлены:
- Docker и Docker Compose
- Создана директория `/home/<user>/foodgram/`

### GitHub Secrets

Для работы CI/CD добавьте в Secrets репозитория (Settings → Secrets and variables → Actions):

| Secret | Описание |
|--------|----------|
| `DOCKER_USERNAME` | Логин Docker Hub |
| `DOCKER_PASSWORD` | Пароль или токен Docker Hub |
| `SERVER_HOST` | IP-адрес сервера |
| `SERVER_USER` | Имя пользователя для SSH |
| `SSH_PRIVATE_KEY` | Приватный SSH-ключ (без пароля) |

### Процесс деплоя

При пуше в ветку `main` GitHub Actions автоматически:

1. Собирает Docker-образы backend и frontend
2. Пушит их на Docker Hub
3. Копирует на сервер: `data/`, `infra/.env`, `infra/nginx.conf`, `infra/docker-compose.prod.yml`, `docs/`
4. На сервере: пуллит образы, запускает контейнеры, выполняет миграции, загружает ингредиенты и создаёт теги

### Ручной деплой

```bash
# 1. Соберите и запушьте образы
docker build -t igorpletnev/foodgram_backend:latest ./backend
docker build -t igorpletnev/foodgram_frontend:latest ./frontend
docker push igorpletnev/foodgram_backend:latest
docker push igorpletnev/foodgram_frontend:latest

# 2. Скопируйте файлы на сервер
scp -r data/ user@server:/home/user/foodgram/
scp infra/.env user@server:/home/user/foodgram/infra/
scp infra/nginx.conf user@server:/home/user/foodgram/infra/
scp infra/docker-compose.prod.yml user@server:/home/user/foodgram/infra/

# 3. Подключитесь к серверу и запустите
ssh user@server
cd /home/user/foodgram/infra
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
docker compose -f docker-compose.prod.yml exec backend python manage.py load_ingredients
```

---

## 👨‍💻 Автор

**Игорь Плетнев**

- GitHub: [@IgorPletnev](https://github.com/IgorPletnev)


