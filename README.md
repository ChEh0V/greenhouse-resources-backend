# Greenhouse Resources

Расчёт требуемых ресурсов для выращивания урожая в теплице на Севере.
Лабораторная работа №4: веб-сервис (REST API) на FastAPI + SQLAlchemy + Alembic, файлы в Minio,
авторизация через сессии в Redis и куку `session_id`, документация Swagger.

## Запуск

```bash
docker compose up -d
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

API: http://127.0.0.1:8000/api, Swagger: http://127.0.0.1:8000/docs, Adminer: http://127.0.0.1:8081.
Коллекция запросов для Postman/Insomnia: `postman/greenhouse_resources.postman_collection.json`.

## Авторизация

После `POST /api/greenhouse_users/login` в Redis создаётся ключ `session:<ид сессии>`
со значением `{"user_id": 2, "login": "chekhovich"}` и сроком жизни 1 час,
а ид сессии возвращается в httpOnly-куке `session_id`.

Без авторизации доступны только методы чтения (1, 2) и регистрация/вход (8, 9) — для гостя
`is_creator` и `is_liked` равны 0. Остальные методы без сессии возвращают 401.
Создатель нового ресурса заполняется из сессии автоматически.

Просмотр сессий в Redis:

```bash
docker exec -it greenhouse_redis redis-cli KEYS "session:*"
docker exec -it greenhouse_redis redis-cli GET session:<ид>
```

## HTTP-методы

### Домен ресурсов теплицы `/api/greenhouse_resources`

| № | Метод | URL | Вход | Выход |
|---|---|---|---|---|
| 1 | GET | `/api/greenhouse_resources` | query `min_value: float` (необязательно) | `[{resource_id, resource_name, image_url, min_value, likes_count, is_creator: 0/1}]` — только опубликованные |
| 2 | GET | `/api/greenhouse_resources/feed` | query `resource_id: int`, `next: bool` (необязательно) | `{resource_id, resource_name, short_description, image_url, video_url, unit, min_value, likes_count, is_liked: 0/1}` — одна опубликованная карточка |
| 3 | GET | `/api/greenhouse_resources/draft` | — | `{resource_id, resource_name, short_description, image_url, video_url, unit, min_value}` — черновик пользователя, 404 если нет |
| 4 | POST | `/api/greenhouse_resources` | form-data `resource_name: str`, `image: file`, `video: file` | 201, черновик (как в п.3); 409 если черновик уже есть |
| 5 | PUT | `/api/greenhouse_resources/{resource_id}/publish` | JSON `{short_description: str, unit: str, min_value: float}` | ресурс (как в п.3), статус draft → published |
| 6 | DELETE | `/api/greenhouse_resources/{resource_id}` | — | 204; логическое удаление только своего ресурса (403 для чужого) |
| 7 | POST | `/api/greenhouse_resources/{resource_id}/like` | JSON `{is_liked: 0/1}` | `{resource_id, likes_count, is_liked}` |

### Домен пользователей `/api/greenhouse_users`

| № | Метод | URL | Вход | Выход |
|---|---|---|---|---|
| 8 | POST | `/api/greenhouse_users/register` | JSON `{login: str, password: str}` | 201, `{user_id, login}`; 409 если логин занят |
| 9 | POST | `/api/greenhouse_users/login` | JSON `{login: str, password: str}` | `{user_id, login}` + кука `session_id`; 401 при неверном пароле |
| 10 | POST | `/api/greenhouse_users/logout` | кука `session_id` | 204, сессия удаляется из Redis |

Ответы об ошибках — только стандартные коды HTTP (400, 401, 403, 404, 409, 422).

## Таблицы

### `greenhouse_users` — пользователи

| Столбец | Тип | Описание |
|---|---|---|
| `user_id` | integer, PK | идентификатор |
| `login` | varchar(64), unique, not null | логин |
| `password` | varchar(128), not null | хеш пароля (PBKDF2-SHA256) |

### `greenhouse_resources` — ресурсы теплицы (услуги)

| Столбец | Тип | Описание |
|---|---|---|
| `resource_id` | integer, PK | идентификатор |
| `resource_name` | varchar(128), not null | наименование ресурса |
| `short_description` | text | краткое описание |
| `resource_status` | varchar(16), not null | `draft` / `published` / `deleted` |
| `image_url` | varchar(256), not null | url изображения в Minio |
| `video_url` | varchar(256), not null | url видео в Minio |
| `unit` | varchar(16) | единица измерения (поле по теме) |
| `min_value` | float | минимальное значение ресурса (поле по теме, фильтр) |
| `created_at` | timestamp, not null | дата создания |
| `published_at` | timestamp | дата формирования (публикации) |
| `creator_id` | integer, FK → `greenhouse_users`, not null | создатель |

### `resource_likes` — лайки (м-м пользователь–ресурс)

| Столбец | Тип | Описание |
|---|---|---|
| `like_id` | integer, PK | идентификатор |
| `user_id` | integer, FK → `greenhouse_users`, not null | кто лайкнул |
| `resource_id` | integer, FK → `greenhouse_resources`, not null | что лайкнули |

Пара (`user_id`, `resource_id`) уникальна. Каскадное удаление запрещено (`ON DELETE RESTRICT`).
