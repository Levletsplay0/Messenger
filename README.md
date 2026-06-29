# Messenger Backend

> **Минимально рабочий бекенд для мессенджера** на основе **FastAPI** с поддержкой групповых чатов, real-time сообщений через WebSocket, аутентификации и работы с базой данных PostgreSQL через SQLAlchemy.

## 🚀 Демо и документация

Проект задеплоен и доступен онлайн. Вы можете интерактивно протестировать API прямо в браузере:

- **Swagger UI:** [http://45.132.255.102:8000/docs](http://45.132.255.102:8000/docs)
- **ReDoc:** [http://45.132.255.102:8000/redoc](http://45.132.255.102:8000/redoc)
- **OpenAPI JSON:** [http://45.132.255.102:8000/openapi.json](http://45.132.255.102:8000/openapi.json)

## 🛠 Технологии

| Компонент | Технология |
|---|---|
| **Фреймворк** | FastAPI |
| **База данных** | PostgreSQL + AsyncPG |
| **ORM** | SQLAlchemy (Async) |
| **Валидация** | Pydantic |
| **Хеширование паролей** | Werkzeug |
| **Контейнеризация** | Docker + Docker Compose |
| **Real-time** | WebSocket |

## ✨ Возможности

- Регистрация и аутентификация пользователей (токены)
- Групповые чаты с возможностью добавления и исключения участников
- **Управление участниками группы** (кик, выход из группы)
- Отправка, редактирование и удаление сообщений
- **Real-time обмен сообщениями** через WebSocket
- Загрузка и удаление аватарок пользователей и групп
- Прикрепление файлов к сообщениям
- Поиск пользователей
- Просмотр профилей пользователей и групп

## 📁 Структура проекта

```
Messenger/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── ws_manager.py
├── constants.py
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 🚀 Установка и запуск

### Вариант 1: Docker Compose (рекомендуется)

Самый быстрый способ запустить проект — вместе с базой данных PostgreSQL.

```bash
git clone https://github.com/Levletsplay0/Messenger.git
cd Messenger
docker compose up -d --build
```

Приложение будет доступно по адресу: **http://localhost:8000**  
Документация API: **http://localhost:8000/docs**

### Вариант 2: Локальный запуск

#### 1. Клонирование репозитория

```bash
git clone https://github.com/Levletsplay0/Messenger.git
cd Messenger
```

#### 2. Создание виртуального окружения и установка зависимостей

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

#### 3. Настройка базы данных

Убедитесь, что PostgreSQL запущена и доступна. По умолчанию приложение подключается к:

```
postgresql+asyncpg://myuser:mypass@localhost:5432/mydb
```

Для изменения подключения задайте переменную окружения `DATABASE_URL`.

#### 4. Запуск

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Документация будет доступна по адресу: **http://127.0.0.1:8000/docs**

## ⚙️ Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `DATABASE_URL` | Строка подключения к PostgreSQL | `postgresql+asyncpg://myuser:mypass@localhost:5432/mydb` |

## 📡 API Endpoints

### Аутентификация и пользователи

| Метод | Эндпоинт | Описание |
|---|---|---|
| `POST` | `/register` | Регистрация нового пользователя |
| `POST` | `/login` | Вход в систему, получение токена |
| `POST` | `/logout` | Выход из системы (инвалидация токена) |
| `GET` | `/users/me` | Информация о текущем пользователе |
| `GET` | `/users/{user_id}` | Информация о пользователе по ID |
| `GET` | `/users/search` | Поиск пользователей по имени |
| `POST` | `/users/me/avatar` | Загрузка аватарки пользователя |
| `DELETE` | `/users/me/avatar` | Удаление аватарки пользователя |
| `PATCH` | `/users/me/description` | Обновление описания профиля |

### Группы

| Метод | Эндпоинт | Описание |
|---|---|---|
| `POST` | `/groups` | Создание новой группы |
| `GET` | `/groups` | Список групп текущего пользователя |
| `GET` | `/groups/{group_id}` | Детали группы |
| `POST` | `/groups/{group_id}/members` | Добавление участников в группу |
| `POST` | `/groups/{group_id}/leave` | Выход из группы |
| `POST` | `/groups/{group_id}/kick` | Исключение участников из группы (только для создателя/админа) |
| `POST` | `/groups/{group_id}/avatar` | Загрузка аватарки группы |
| `DELETE` | `/groups/{group_id}/avatar` | Удаление аватарки группы |
| `PATCH` | `/groups/{group_id}/name` | Изменение названия группы |
| `PATCH` | `/groups/{group_id}/description` | Изменение описания группы |

### Сообщения

| Метод | Эндпоинт | Описание |
|---|---|---|
| `POST` | `/groups/{group_id}/messages` | Отправка сообщения (с файлом) |
| `GET` | `/groups/{group_id}/messages` | Получение истории сообщений |
| `PATCH` | `/groups/{group_id}/messages/{message_id}` | Редактирование сообщения |
| `DELETE` | `/groups/{group_id}/messages/{message_id}` | Удаление сообщения |

### WebSocket

| Протокол | Эндпоинт | Описание |
|---|---|---|
| `WS` | `/ws/{group_id}?token=<auth_token>` | Real-time обмен сообщениями в группе |

## 🔌 WebSocket

WebSocket-соединение позволяет получать и отправлять сообщения в реальном времени.

### Подключение

```
ws://localhost:8000/ws/{group_id}?token=<your_auth_token>
```

### Формат сообщений

**Отправка сообщения:**
```json
{
  "action": "send_message",
  "content": "Привет!"
}
```

**Редактирование сообщения:**
```json
{
  "action": "edit_message",
  "message_id": 1,
  "content": "Привет, мир!"
}
```

**Удаление сообщения:**
```json
{
  "action": "delete_message",
  "message_id": 1
}
```

## 📋 Примеры запросов

### Регистрация пользователя

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secure123", "email": "alice@example.com"}'
```

**Ответ:**
```json
{
  "success": true,
  "message": "Пользователь успешно создан",
  "data": {
    "id": 1,
    "username": "alice"
  }
}
```

---

### Вход в систему

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secure123"}'
```

**Ответ:**
```json
{
  "success": true,
  "message": "Успешный вход",
  "data": {
    "auth_token": "a1b2c3d4e5f6..."
  }
}
```

---

### Информация о себе

```bash
curl -X GET http://localhost:8000/users/me \
  -H "auth-token: a1b2c3d4e5f6..."
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com"
  }
}
```

---

### Создание группы

```bash
curl -X POST http://localhost:8000/groups \
  -H "auth-token: a1b2c3d4e5f6..." \
  -H "Content-Type: application/json" \
  -d '{"name": "Моя группа"}'
```

---

### Отправка сообщения в группу

```bash
curl -X POST http://localhost:8000/groups/1/messages \
  -H "auth-token: a1b2c3d4e5f6..." \
  -F "content=Привет, группа!"
```

---

### Выход из группы

```bash
curl -X POST http://localhost:8000/groups/1/leave \
  -H "auth-token: a1b2c3d4e5f6..."
```

**Ответ:**
```json
{
  "success": true,
  "message": "Вы вышли из группы",
  "data": {
    "group_id": 1
  }
}
```

---

### Исключение участников из группы (kick)

Доступно только **создателю группы** или **админу**. Админ не может кикнуть другого админа или создателя.

```bash
curl -X POST http://localhost:8000/groups/1/kick \
  -H "auth-token: a1b2c3d4e5f6..." \
  -H "Content-Type: application/json" \
  -d '{"user_ids": [3, 5, 7]}'
```

**Ответ (успех):**
```json
{
  "success": true,
  "message": "Исключено 3 участников",
  "data": {
    "group_id": 1,
    "kicked_count": 3,
    "kicked_user_ids": [3, 5, 7],
  }
}
```

**Ответ (ошибка прав):**
```json
{
  "success": false,
  "message": "Только создатель или админ может исключать участников"
}
```

---

> **Автор:** [@Levletsplay0](https://github.com/Levletsplay0)  
> **Поставьте ⭐, если проект был полезен!**