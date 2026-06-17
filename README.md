Foodgram – это веб-приложение, где пользователи могут делиться своими рецептами, добавлять чужие рецепты в избранное, подписываться на авторов и формировать список покупок. Проект демонстрирует полный цикл разработки и развёртывания: бэкенд на Django + DRF, фронтенд на React, обратный прокси‑сервер Nginx, база данных PostgreSQL. Все компоненты упакованы в Docker‑контейнеры, а автоматическое тестирование и деплой настроены через GitHub Actions.

**Польза проекта:**
- Готовый шаблон для создания подобных кулинарных платформ.
- Практический пример контейнеризации и CI/CD.
- Отработка навыков работы с Docker, Docker Compose, GitHub Actions, Nginx, PostgreSQL.

---

# Установка и запуск

## Локальный запуск (для разработки)

1. Клонируйте репозиторий:
```
git clone https://github.com/IgorPletnev/foodgram.git
```

```
cd foodgram
```
2. Создайте и активируйте виртуальное окружение:
```
python -m venv venv
```

```
source venv/bin/activate   # для Linux/Mac
source venv\Scripts\activate      # для Windows
```
3. Установите зависимости:
```
pip install -r backend/requirements.txt
```
4. Настройте переменные окружения:
Создайте .env в папке infra (PostgreSQL, секретный ключ Django и т.д.).
5. Выполните миграции:
```
python backend/manage.py migrate
```
6. Запустите бэкенд и фронтенд:
```
python backend/manage.py runserver 0.0.0.0:8000
cd frontend && npm start
```

