README.md

# Итоговый проект. Двухсервисная система LLM-консультаций

## Описание проекта

В этом проекте я сделал систему из двух отдельных сервисов:

1. Auth Service — отвечает за регистрацию, логин и выдачу JWT-токена
2. Bot Service — Telegram-бот, который принимает JWT, проверяет его и только после этого даёт доступ к LLM

Смысл архитектуры в том, что сервисы разделены по ролям:

- Auth Service работает только с пользователями и токенами
- Bot Service не хранит пользователей и не делает логин
- JWT создаётся только в Auth Service
- Bot Service только проверяет токен и использует его для доступа к модели

Это приближено к нормальной микросервисной архитектуре.

---

## Что делает система

Сценарий работы такой:

1. Пользователь регистрируется в Auth Service
2. Потом логинится и получает JWT
3. Отправляет этот JWT Telegram-боту через команду `/token <jwt>`
4. Бот сохраняет токен в Redis
5. Когда пользователь отправляет обычный текст, бот проверяет токен
6. Если токен валиден, бот не идёт в LLM напрямую, а ставит задачу в RabbitMQ через Celery
7. Celery worker забирает задачу, идёт в OpenRouter и получает ответ
8. После этого worker отправляет результат пользователю в Telegram

---

## Архитектура проекта

### 1. Auth Service

Отдельный сервис на FastAPI.

Он отвечает за:
- регистрацию пользователя
- логин пользователя
- хеширование пароля
- выпуск JWT
- получение профиля по токену

Используемые технологии:
- FastAPI
- SQLAlchemy Async
- SQLite
- python-jose
- passlib[bcrypt]
- pytest
- httpx

Основные endpoint:
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /health`

JWT содержит поля:
- `sub`
- `role`
- `iat`
- `exp`

---

### 2. Bot Service

Отдельный сервис для Telegram-бота.

Он отвечает за:
- приём JWT от пользователя
- проверку JWT
- хранение JWT в Redis
- отправку задач в RabbitMQ
- получение ответа от LLM через Celery worker
- возврат ответа пользователю в Telegram

Используемые технологии:
- aiogram
- FastAPI
- Celery
- RabbitMQ
- Redis
- httpx
- python-jose
- pytest
- fakeredis
- respx

Команды бота:
- `/start`
- `/token <jwt>`

Route:
- `GET /health`

---

## Почему это считается правильной реализацией

В этой работе сервисы реально разделены:

- Auth Service не знает ничего про Telegram-бота
- Bot Service не содержит регистрацию и логин
- Bot Service не ходит напрямую в базу Auth Service
- JWT создаётся только в Auth Service
- Bot Service только валидирует токен локально

Также запросы к модели не делаются прямо в Telegram handler.
Сначала задача ставится в очередь, потом её обрабатывает Celery worker.
Из-за этого бот не зависает и остаётся отзывчивым.

---

## Структура проекта

```bash
project-root/
├─ auth_service/
├─ bot_service/
└─ README.md
```

### Структура Auth Service

- `app/main.py` — создание FastAPI приложения
- `app/core/config.py` — настройки
- `app/core/security.py` — работа с хешированием и JWT
- `app/core/exceptions.py` — кастомные ошибки
- `app/db/base.py` — базовый ORM класс
- `app/db/session.py` — engine и sessionmaker
- `app/db/models.py` — модель пользователя
- `app/schemas/auth.py` — схемы регистрации и токена
- `app/schemas/user.py` — публичная схема пользователя
- `app/repositories/users.py` — репозиторий пользователей
- `app/usecases/auth.py` — бизнес-логика
- `app/api/deps.py` — зависимости FastAPI
- `app/api/routes_auth.py` — роуты авторизации
- `tests/` — тесты

### Структура Bot Service

- `app/main.py` — FastAPI приложение
- `app/core/config.py` — настройки
- `app/core/jwt.py` — проверка JWT
- `app/infra/redis.py` — Redis client
- `app/infra/celery_app.py` — Celery app
- `app/services/openrouter_client.py` — клиент OpenRouter
- `app/tasks/llm_tasks.py` — Celery-задача
- `app/bot/dispatcher.py` — сборка бота
- `app/bot/handlers.py` — Telegram handlers
- `app/bot/run.py` — запуск polling
- `tests/` — тесты

---

## Переменные окружения

### Auth Service `.env`
```bash
APP_NAME=auth-service
ENV=local

JWT_SECRET=change_me_super_secret
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

SQLITE_PATH=./auth.db
```

### Bot Service `.env`

```bash
APP_NAME=bot-service
ENV=local

TELEGRAM_BOT_TOKEN=Сюда токен из BotFather
AUTH_SERVICE_URL=http://127.0.0.1:8000

JWT_SECRET=change_me_super_secret
JWT_ALG=HS256

REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672//

OPENROUTER_API_KEY=Сюда токен из openrouter
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openrouter/auto
OPENROUTER_SITE_URL=https://example.com
OPENROUTER_APP_NAME=bot-service
```

---

## Как запускать проект

### 1. Запуск Auth Service

```bash
cd auth_service
uv venv
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger:
- `http://127.0.0.1:8000/docs`

### 2. Запуск инфраструктуры для Bot Service

```bash
cd bot_service
docker compose up -d
```

RabbitMQ UI:
- `http://127.0.0.1:15672`
- login: `guest`
- password: `guest`

### 3. Запуск FastAPI части Bot Service

```bash
cd bot_service
py -m uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 4. Запуск Celery worker

```bash
cd bot_service
py -m uv run celery -A app.infra.celery_app:celery_app worker --loglevel=info --pool=solo
```

### 5. Запуск Telegram-бота

```bash
cd bot_service
py -m uv run python -m app.bot.run
```

---

## Пользовательский сценарий

1. Пользователь регистрируется в Auth Service
2. Пользователь логинится и получает JWT
3. Отправляет токен боту командой `/token <jwt>`
4. После этого отправляет обычный вопрос
5. Бот принимает запрос
6. Задача уходит в RabbitMQ
7. Worker получает задачу
8. Worker идёт в OpenRouter
9. Ответ приходит пользователю в Telegram

---

## Тестирование

### Auth Service

Сделаны:
- unit tests для security.py
- integration tests для register, login и me
- негативные тесты для ошибок авторизации

Команда запуска:
```bash
cd auth_service
uv run pytest -v
```

### Bot Service

Сделаны:
- unit tests для JWT
- mock tests для Telegram handlers
- integration tests для OpenRouter клиента

Команда запуска:
```bash
cd bot_service
py -m uv run pytest -v
```

---

## Результат

В итоге получилась рабочая двухсервисная система:

- Auth Service выпускает JWT и работает с пользователями
- Bot Service отдельно работает как Telegram-бот
- Bot Service не хранит пользователей
- Bot Service валидирует JWT локально
- Redis реально используется для хранения токена пользователя
- RabbitMQ реально используется для очередей
- Celery worker реально обрабатывает задачу
- запрос к LLM не выполняется прямо в handler
- ключевые части проекта покрыты тестами

---

## Что приложено к работе

### Скриншоты Auth Service

1. Регистрация пользователя через Swagger  
![img_1.png](img_1.png)

2. Логин через Swagger  
![img_2.png](img_2.png)

3. Получение профиля по токену  
![img_3.png](img_3.png)

4. Проверка health endpoint  
![img.png](img.png)

### Скриншоты Telegram-бота

5. Команда `/start`
6. Передача JWT через `/token <jwt>`
7. Отправка обычного вопроса
8. Ответ модели пользователю
![img_4.png](img_4.png)

### Скриншоты RabbitMQ

9. Overview  
![img_5.png](img_5.png)

10. Очереди / Queues and Streams  
![img_6.png](img_6.png)

11. Подключения / consumers / активность сообщений  
![img_7.png](img_7.png)

### Скриншоты тестов

12. Тесты Auth Service  
![img_9.png](img_9.png)

13. Тесты Bot Service  
![img_8.png](img_8.png)

---

## Короткий вывод

В этой работе я реализовал двухсервисную систему LLM-консультаций с разделением ответственности между сервисами.

Auth Service отвечает только за регистрацию, логин и выпуск JWT.  
Bot Service работает отдельно, принимает JWT, валидирует его и даёт доступ к LLM только после успешной проверки токена.

Для асинхронной обработки запросов использованы RabbitMQ, Redis и Celery.  
За счёт этого запросы к модели выполняются не прямо в Telegram-обработчике, а в отдельном worker-процессе.

Также для обоих сервисов написаны тесты, которые проверяют основную логику работы системы.
