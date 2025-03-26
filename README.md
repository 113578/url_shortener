# URL Shortener
URL Shortener — это сервис для сокращения URL, управления ими и получения статистики.

## Описание API
API предоставляет следующие возможности:
- Регистрация и аутентификация пользователей.
- Создание коротких URL.
- Перенаправление по короткому URL.
- Обновление и удаление коротких URL.
- Получение статистики по URL.
- Управление проектами и просмотр истекших URL.

## Примеры запросов
### 1. Регистрация пользователя
**POST** `/auth/register`

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

### 2. Создание короткого URL
**POST** `/links/shorten`

```json
{
  "url": "https://example.com",
  "lifetime": 3600,
  "alias": "example",
  "project_name": "project1"
}
```

### 3. Перенаправление по короткому URL
**GET** `/links/{alias}`

Ответ: Перенаправление на оригинальный URL.

### 4. Получение статистики по URL
**GET** `/links/{alias}/stats`

Ответ:
```json
{
  "url": "https://example.com",
  "created_at": "2023-01-01T12:00:00",
  "clicks_count": 10,
  "last_clicked_at": "2023-01-02T12:00:00"
}
```

### 5. Удаление URL
**DELETE** `/links/delete/{alias}`

Ответ: HTTP 204 No Content.

## Инструкция по запуску
1. Убедитесь, что у вас установлен Docker и Docker Compose.
2. Склонируйте репозиторий:
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```
3. Создайте файл `.env` на основе `.env.example` и заполните его.
4. Запустите сервисы:
   ```bash
   docker-compose up --build
   ```
5. API будет доступен по адресу: `http://localhost:8000`.

## Описание БД
База данных состоит из следующих таблиц:

### 1. `users`
- **id**: UUID, уникальный идентификатор пользователя.
- **email**: Email пользователя.
- **hashed_password**: Хэш пароля.
- **created_at**: Дата создания пользователя.

### 2. `current_urls`
- **id**: Уникальный идентификатор записи.
- **user_id**: ID пользователя, создавшего URL.
- **url**: Оригинальный URL.
- **alias**: Короткий URL (алиас).
- **created_at**: Дата создания.
- **expire_at**: Дата истечения срока действия.
- **clicks_count**: Количество кликов по URL.
- **last_clicked_at**: Дата последнего клика.
- **project_name**: Название проекта.
- **celery_task_id**: ID задачи Celery.

### 3. `deleted_urls`
- **id**: Уникальный идентификатор записи.
- **user_id**: ID пользователя, удалившего URL.
- **url**: Оригинальный URL.
- **alias**: Короткий URL (алиас).
- **created_at**: Дата создания.
- **expired_at**: Дата истечения срока действия.
- **clicks_count**: Количество кликов по URL.
- **last_clicked_at**: Дата последнего клика.
- **project_name**: Название проекта.

## Дополнительно
- Документация API доступна по адресу: `http://localhost:8000/docs`.
- Для проверки кода используйте скрипты линтеров в папке `app/utils/linters`.
