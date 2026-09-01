# Messenger Backend

> **Минимально рабочий бекенд для мессенджера** на основе **FastAPI** с поддержкой групповых чатов, real-time сообщений через WebSocket, аутентификации и работы с базой данных PostgreSQL через SQLAlchemy.

> 🚧 **Проект заморожен**  
> Разработка временно приостановлена, так как автор ушел с головой в учебу.  
> ⚠️ **Важно:** Тестовый сервер скоро будет отключен из-за окончания оплаты хостинга. Пожалуйста, запускайте проект локально (инструкции ниже).
> 
> **Это отличная возможность внести вклад!** Задач много: от полировки кода и добавления новых фич до оптимизации работы с базой данных. Можешь прямо сейчас сделать форк, реализовать фичу и отправить pull request. Или напиши мне в Telegram по поводу проекта, и я отвечу на все вопросы: [@Levletsplay](https://t.me/Levletsplay)


## 🚀 Демо и документация

Проект задеплоен, но скоро сервер будет отключен из-за того, что я не оплачиваю хостинг. Если демо перестанет работать, запускайте локально. Инструкции ниже.

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
- Отправка, редактирование и удаление сообщений (**поддержка отправки файла**)
- **Real-time обмен сообщениями** через WebSocket (включая статусы "печатает...")
- Загрузка и удаление аватарок пользователей и групп
- Прикрепление файлов к сообщениям
- Поиск пользователей **с пагинацией**
- Просмотр профилей пользователей и групп
- **Редактирование профилей** (описание пользователя, название, описание и аватар группы)
- **Имя и фамилия** при регистрации
- Отдача загруженных файлов (аватарок и вложений) по прямым ссылкам через статический роутинг
- **Удаление группы** (только создателем, с автоматической очисткой всех файлов группы)

## 📁 Структура проекта

```text
Messenger/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── ws_manager.py
├── constants.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── routers/
│   ├── auth.py
│   ├── users.py
│   ├── groups.py
│   └── ws.py
└── services/
    ├── auth.py
    ├── user.py
    ├── group.py
    ├── message.py
    └── ws.py
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

#### 5. Проверьте работу бэкенда:
```bash
curl -X GET http://127.0.0.1:8000/ \
  -H "Content-Type: application/json" \
```
Должен вернуть:
```json
{
  "success": true,
  "message": "Прекрасно, бэкенд мессенджера работает!",
  "data": {
    "version": "1.0.0",
    "time": "2026-07-25T14:30:00.123456",
    "docs": "/docs"
  }
}
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
| `GET` | `/groups/{group_id}/members` | **Список участников группы** (с ролями и датой вступления) | - |
| `POST` | `/groups/{group_id}/members` | Добавление участников в группу | `user_ids` (список ID) |
| `POST` | `/groups/{group_id}/leave` | Выход из группы | - |
| `POST` | `/groups/{group_id}/kick` | Исключение участников (только создатель/админ) | `user_ids` (список ID) |
| `DELETE`| `/groups/{group_id}` | **Удаление группы** (только создатель) | - |
| `POST` | `/groups/{group_id}/avatar` | Загрузка аватарки группы *(доступно любому участнику)* | Form: `file` (png, jpg, jpeg, webp) |
| `DELETE` | `/groups/{group_id}/avatar` | Удаление аватарки группы *(доступно любому участнику)* | - |
| `PATCH` | `/groups/{group_id}/name` | Изменение названия группы *(доступно любому участнику)* | `name` (от 5 до 20 символов) |
| `PATCH` | `/groups/{group_id}/description` | Изменение описания группы *(доступно любому участнику)* | `description` (макс. 100 символов) |

### Сообщения

| Метод | Эндпоинт | Описание | Параметры (Body/Query) |
|---|---|---|---|
| `POST` | `/groups/{group_id}/messages` | Отправка сообщения | Form: `content` (опционально*), `file` (опционально*) |
| `GET` | `/groups/{group_id}/messages` | Получение истории сообщений | Query: `limit` (по умолч. 20), `offset` |
| `PATCH` | `/groups/{group_id}/messages/{message_id}` | Редактирование сообщения (макс. 5000 символов) | `content` |
| `DELETE` | `/groups/{group_id}/messages/{message_id}` | Удаление сообщения | - |

> *\*Как минимум один из параметров (`content` или `file`) должен быть заполнен. Теперь можно отправить сообщение, состоящее только из файла.*

### WebSocket

| Протокол | Эндпоинт | Описание |
|---|---|---|
| `WS` | `/ws/{group_id}?token=<auth_token>` | Real-time обмен сообщениями и статусами в группе |

## 📂 Статические файлы
Все загруженные файлы (аватарки пользователей, аватарки групп, файлы из сообщений) сохраняются в локальную директорию `static/` и доступны по прямым ссылкам.  
Например, если в ответе API пришел `avatar_path: "static/user_avatars/1_abc.png"`, вы можете получить изображение по адресу:  
`http://localhost:8000/static/user_avatars/1_abc.png`

## 🔌 WebSocket

WebSocket-соединение позволяет получать и отправлять сообщения в реальном времени.  
> **Важно:** Через WebSocket можно отправлять **только текст**. Для отправки файлов используйте HTTP `POST /groups/{group_id}/messages`.

### Подключение

```text
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
  "data": { ... } // полные данные сообщения или объект с user_id и username
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

### Создание группы

```bash
curl -X POST http://localhost:8000/groups \
  -H "auth-token: a1b2c3d4e5f6..." \
  -H "Content-Type: application/json" \
  -d '{"name": "Моя группа"}'
```

---

### Получение списка участников группы

```bash
curl -X GET http://localhost:8000/groups/1/members \
  -H "auth-token: a1b2c3d4e5f6..."
```

**Ответ:**
```json
{
  "success": true,
  "message": "Участники получены",
  "data": [
    {
      "id": 1,
      "username": "alice",
      "name": "Алиса",
      "last_name": "Селезнева",
      "avatar_path": "static/user_avatars/1_abc123.png",
      "description": "Люблю программировать",
      "role": "creator",
      "joined_at": "2026-06-30T12:00:00"
    }
  ]
}
```

---

### Отправка сообщения в группу (только файл, без текста)

```bash
curl -X POST http://localhost:8000/groups/1/messages \
  -H "auth-token: a1b2c3d4e5f6..." \
  -F "file=@document.pdf"
```

**Ответ:**
```json
{
  "success": true,
  "message": "Сообщение отправлено",
  "data": {
    "id": 1,
    "content": null,
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

### Удаление группы

```bash
curl -X DELETE http://localhost:8000/groups/1 \
  -H "auth-token: a1b2c3d4e5f6..."
```

**Ответ:**
```json
{
  "success": true,
  "message": "Группа успешно удалена",
  "data": {
    "id": 1,
    "name": "Моя группа",
    "creator_id": 1
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

---

> **Автор:** [@Levletsplay0](https://github.com/Levletsplay0)  
> **Поставьте ⭐, если проект был полезен!**