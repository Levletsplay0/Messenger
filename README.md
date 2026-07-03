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
- **Управление участниками группы** (кик, выход из группы, роли: создатель/админ/участник)
- Отправка, редактирование и удаление сообщений
- **Real-time обмен сообщениями** через WebSocket
- Загрузка и удаление аватарок пользователей и групп
- Прикрепление файлов к сообщениям
- Поиск пользователей **с пагинацией**
- Просмотр профилей пользователей и групп
- **Редактирование профилей** (описание пользователя, название и описание группы)
- **Имя и фамилия** при регистрации
- Отдача загруженных файлов (аватарок и вложений) по прямым ссылкам через статический роутинг

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

Самый быстрый способ запустить проект вместе с базой данных PostgreSQL.

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

> **Примечание:** Аутентификация во всех защищенных эндпоинтах происходит через заголовок `auth-token`.
> Все ответы API имеют единый формат: `{"success": true/false, "message": "...", "data": ...}`.

### Аутентификация и пользователи

| Метод | Эндпоинт | Описание | Параметры (Body/Query) |
|---|---|---|---|
| `POST` | `/register` | Регистрация нового пользователя | `username`, `password`, `email`, `name`, `last_name` |
| `POST` | `/login` | Вход в систему, получение токена | `username`, `password` |
| `POST` | `/logout` | Выход из системы (инвалидация токена) | - |
| `GET` | `/users/me` | Информация о текущем пользователе | - |
| `GET` | `/users/{user_id}` | Просмотр профиля другого пользователя | - |
| `GET` | `/users/search` | Поиск пользователей по имени | Query: `username`, `limit` (по умолч. 20), `offset` |
| `POST` | `/users/me/avatar` | Загрузка аватарки пользователя | Form: `file` (png, jpg, jpeg, webp) |
| `DELETE` | `/users/me/avatar` | Удаление аватарки пользователя | - |
| `PATCH` | `/users/me/description` | Обновление описания профиля (макс. 100 символов) | `description` |

### Группы

| Метод | Эндпоинт | Описание | Параметры (Body/Query) |
|---|---|---|---|
| `POST` | `/groups` | Создание новой группы | `name` (от 5 до 20 символов) |
| `GET` | `/groups` | Список групп текущего пользователя | - |
| `GET` | `/groups/{group_id}` | Детали группы | - |
| `POST` | `/groups/{group_id}/members` | Добавление участников в группу | `user_ids` (список ID) |
| `POST` | `/groups/{group_id}/leave` | Выход из группы | - |
| `POST` | `/groups/{group_id}/kick` | Исключение участников (только создатель/админ) | `user_ids` (список ID) |
| `POST` | `/groups/{group_id}/avatar` | Загрузка аватарки группы | Form: `file` (png, jpg, jpeg, webp) |
| `DELETE` | `/groups/{group_id}/avatar` | Удаление аватарки группы | - |
| `PATCH` | `/groups/{group_id}/name` | Изменение названия группы (от 5 до 20 символов) | `name` |
| `PATCH` | `/groups/{group_id}/description` | Изменение описания группы (макс. 100 символов) | `description` |

### Сообщения

| Метод | Эндпоинт | Описание | Параметры (Body/Query) |
|---|---|---|---|
| `POST` | `/groups/{group_id}/messages` | Отправка сообщения (с файлом) | Form: `content`, `file` |
| `GET` | `/groups/{group_id}/messages` | Получение истории сообщений | Query: `limit` (по умолч. 20), `offset` |
| `PATCH` | `/groups/{group_id}/messages/{message_id}` | Редактирование сообщения (макс. 5000 символов) | `content` |
| `DELETE` | `/groups/{group_id}/messages/{message_id}` | Удаление сообщения | - |

### WebSocket

| Протокол | Эндпоинт | Описание |
|---|---|---|
| `WS` | `/ws/{group_id}?token=<auth_token>` | Real-time обмен сообщениями в группе |

## 📂 Статические файлы
Все загруженные файлы (аватарки пользователей, аватарки групп, файлы из сообщений) сохраняются в локальную директорию `static/` и доступны по прямым ссылкам.
Например, если в ответе API пришел `avatar_path: "static/user_avatars/1_abc.png"`, вы можете получить изображение по адресу:
`http://localhost:8000/static/user_avatars/1_abc.png`

## 🔌 WebSocket

WebSocket-соединение позволяет получать и отправлять сообщения в реальном времени. 
> **Важно:** Через WebSocket можно отправлять **только текст**. Для отправки файлов используйте HTTP `POST /groups/{group_id}/messages`.

### Подключение

```
ws://localhost:8000/ws/{group_id}?token=<your_auth_token>
```

### Формат сообщений (Клиент -> Сервер)

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

**Разослать всем "Печатает..."**
```json
{
  "action": "typing"
}
```

**Перестать "Печатать"**
```json
{
  "action": "stop_typing"
}
```

### Ответы сервера (Broadcast)
Сервер автоматически рассылает обновления всем подключенным участникам группы:
```json
{
  "type": "new_message", // или "edit_message", "delete_message", "typing", "stop_typing"
  "data": { ... } // полные данные сообщения или user_id и username
}
```

## 📋 Примеры запросов

### Регистрация пользователя

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice", 
    "password": "secure123", 
    "email": "alice@example.com",
    "name": "Алиса",
    "last_name": "Селезнева"
  }'
```

**Ответ:**
```json
{
  "success": true,
  "message": "Пользователь успешно создан",
  "data": {
    "id": 1,
    "username": "alice",
    "name": "Алиса",
    "last_name": "Селезнева"
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

### Информация о себе (Профиль)

```bash
curl -X GET http://localhost:8000/users/me \
  -H "auth-token: a1b2c3d4e5f6..."
```

**Ответ:**
```json
{
  "success": true,
  "message": "Пользователь найден",
  "data": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "name": "Алиса",
    "last_name": "Селезнева",
    "avatar_path": "static/user_avatars/1_abc123.png",
    "description": "Люблю программировать"
  }
}
```

---

### Обновление описания профиля

```bash
curl -X PATCH http://localhost:8000/users/me/description \
  -H "auth-token: a1b2c3d4e5f6..." \
  -H "Content-Type: application/json" \
  -d '{"description": "Новое описание обо мне"}'
```

---

### Создание группы

```bash
curl -X POST http://localhost:8000/groups \
  -H "auth-token: a1b2c3d4e5f6..." \
  -H "Content-Type: application/json" \
  -d '{"name": "Моя группа"}'
```

**Ответ:**
```json
{
  "success": true,
  "message": "Группа успешно создана",
  "data": {
    "id": 1,
    "name": "Моя группа",
    "creator_id": 1,
    "created_at": "2026-06-30T12:00:00"
  }
}
```

---

### Добавление участников в группу

```bash
curl -X POST http://localhost:8000/groups/1/members \
  -H "auth-token: a1b2c3d4e5f6..." \
  -H "Content-Type: application/json" \
  -d '{"user_ids": [2, 3]}'
```

---

### Отправка сообщения в группу (с файлом)

```bash
curl -X POST http://localhost:8000/groups/1/messages \
  -H "auth-token: a1b2c3d4e5f6..." \
  -F "content=Привет, группа!" \
  -F "file=@document.pdf"
```

**Ответ:**
```json
{
  "success": true,
  "message": "Сообщение отправлено",
  "data": {
    "id": 1,
    "content": "Привет, группа!",
    "author_id": 1,
    "author_username": "alice",
    "author_avatar_path": "static/user_avatars/1_abc123.png",
    "group_id": 1,
    "sent_at": "2026-06-30T12:05:00",
    "file": {
      "path": "static/message_files/abc123.pdf",
      "name": "document.pdf",
      "size": 102400
    }
  }
}
```

---

### Получение истории сообщений (с пагинацией)

```bash
curl -X GET "http://localhost:8000/groups/1/messages?limit=20&offset=0" \
  -H "auth-token: a1b2c3d4e5f6..."
```

**Ответ:**
```json
{
  "success": true,
  "message": "Загружено 1 сообщений",
  "data": [
    {
      "id": 1,
      "content": "Привет, группа!",
      "author_id": 1,
      "author_username": "alice",
      "author_avatar_path": "static/user_avatars/1_abc123.png",
      "group_id": 1,
      "sent_at": "2026-06-30T12:05:00",
      "edited_at": null,
      "file": {
        "path": "static/message_files/abc123.pdf",
        "name": "document.pdf",
        "size": 102400
      }
    }
  ]
}
```

---

### Редактирование сообщения

```bash
curl -X PATCH http://localhost:8000/groups/1/messages/1 \
  -H "auth-token: a1b2c3d4e5f6..." \
  -H "Content-Type: application/json" \
  -d '{"content": "Привет, группа! (отредактировано)"}'
```

---

### Просмотр профиля другого пользователя

```bash
curl -X GET http://localhost:8000/users/2 \
  -H "auth-token: a1b2c3d4e5f6..."
```

**Ответ:**
```json
{
  "success": true,
  "message": "Пользователь найден",
  "data": {
    "id": 2,
    "username": "bob",
    "name": "Боб",
    "last_name": "Большой",
    "description": "Привет, я Боб",
    "avatar_path": null
  }
}
```

---

### Просмотр деталей группы

```bash
curl -X GET http://localhost:8000/groups/1 \
  -H "auth-token: a1b2c3d4e5f6..."
```

**Ответ:**
```json
{
  "success": true,
  "message": "Группа найдена",
  "data": {
    "id": 1,
    "name": "Моя группа",
    "description": "Описание группы",
    "avatar_path": null,
    "creator_id": 1,
    "created_at": "2026-06-30T12:00:00"
  }
}
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
    "group_id": 1,
    "user_id": 1,
    "username": "alice"
  }
}
```

---

### Исключение участников из группы (kick)

Доступно только **создателю группы** или **админу**. 
- Админ не может кикнуть другого админа или создателя.
- Админ может исключать только обычных участников.

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
    "kicked_user_ids": [3, 5, 7]
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