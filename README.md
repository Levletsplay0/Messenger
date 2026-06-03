# Messenger Backend

> **Минимально рабочий бекенд для мессенджера** на основе **FastAPI** с поддержкой групповых чатов, аутентификации и работы с базой данных.


## 🛠 Технологии

| Компонент | Технология |
|-----------|-----------|
| **Фреймворк** | FastAPI |
| **База данных** | PostgreSQL + AsyncPG |
| **ORM** | SQLAlchemy (Async) |
| **Валидация** | Pydantic |
| **Хеширование паролей** | Werkzeug |


## 🚀 Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/Levletsplay0/Messenger.git
cd Messenger
```

### 2. Создание виртуального окружения и установка зависимостей

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Запуск

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Документация будет доступна по адресу: http://127.0.0.1:8000/docs

## Примеры запросов
### Регистрация пользователя
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secure123", "email": "alice@example.com"}'
```
### Ответ
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

### Ответ
```json
{
  "success": true,
  "message": "Успешный вход",
  "data": {
    "access_token": "a1b2c3d4e5f6..."
  }
}
```

---

### Информация о себе
```bash
curl -X GET http://localhost:8000/users/me \
  -H "auth-token: a1b2c3d4e5f6..." \
```

### Ответ
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

## План развития

- [x] Web Socket и real time

- [ ] Управление сообщениями (удаление, изменение, мб реакции)

- [ ] Рефакторинг кода


> Автор: [@Levletsplay0 ](https://github.com/Levletsplay0)  
**Поставьте звезду, если проект помог!**
