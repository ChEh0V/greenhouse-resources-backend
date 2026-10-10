# Greenhouse Resources

Расчёт требуемых ресурсов для выращивания урожая в теплице на Севере.
Лабораторная работа №2: PostgreSQL, SQLAlchemy ORM, миграции Alembic.

## Запуск

```bash
docker compose up -d
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

Приложение: http://127.0.0.1:8000, Adminer: http://127.0.0.1:8081
(сервер `postgres`, пользователь/пароль/БД — `greenhouse`/`greenhouse`/`greenhouse_db`).

## HTTP-методы

| Метод | URL | Контроллер | Назначение |
|---|---|---|---|
| GET | `/greenhouse_resources/feed` | `resource_feed` | лента, `?resource_id=N`, `?next=true` — из БД одна строка |
| GET | `/greenhouse_resources/draft` | `resource_draft` | черновик пользователя |
| GET | `/greenhouse_resources` | `resource_grid` | плитка, фильтр `?min_value=N` |
| POST | `/greenhouse_resources/create` | `create_resource` | «Далее» — создание черновика (ORM) |
| POST | `/greenhouse_resources/publish` | `publish_resource` | «Опубликовать» (ORM) |
| POST | `/greenhouse_resources/delete` | `delete_resource` | логическое удаление через SQL-курсор |

## Таблицы

* `greenhouse_users` — пользователи: `user_id`, `login`, `password`
* `greenhouse_resources` — ресурсы теплицы (услуги): `resource_id`, `resource_name`,
  `short_description`, `resource_status` (draft/published/deleted), `image_url`, `video_url`,
  `unit` (единица измерения), `min_value` (минимальное значение), `created_at`,
  `published_at` (дата формирования), `creator_id`
* `resource_likes` — лайки, м-м пользователь–ресурс: `like_id`, `user_id`, `resource_id`

Файлы ресурсов — Minio, бакет `greenhouse`. Изображение и видео по умолчанию
хранятся на сервере: `static/img/default_resource.jpg`, `static/video/default_resource.mp4`.
