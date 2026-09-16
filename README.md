# Greenhouse Resources

Расчёт требуемых ресурсов для выращивания урожая в теплице на Севере.

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Приложение: http://127.0.0.1:8000

## Страницы

| URL | Контроллер | Назначение |
|---|---|---|
| `/greenhouse_resources/feed` | `resource_feed` | лента, `?resource_id=N`, `?next=true` |
| `/greenhouse_resources/draft` | `resource_draft` | услуга в статусе черновик |
| `/greenhouse_resources` | `resource_grid` | плитка, `?min_value=N` |

Хранилище файлов — Minio, бакет `greenhouse`.
