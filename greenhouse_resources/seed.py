"""Создание таблиц и наполнение начальными данными."""

from datetime import datetime

from greenhouse_resources.models import (
    Base, GreenhouseResource, GreenhouseUser, ResourceLike, SessionLocal,
    STATUS_DELETED, STATUS_DRAFT, STATUS_PUBLISHED, build_minio_url, engine,
)

SEED_RESOURCES = [
    ("Площадь теплицы", "Полезная площадь под посадку.",
     STATUS_PUBLISHED, "greenhouse_frame", "м²", 8.0),
    ("Электроэнергия", "Досветка растений в период короткого светового дня.",
     STATUS_PUBLISHED, "led_lighting", "кВт·ч", 45.0),
    ("Тепловая энергия", "Обогрев теплицы в зимний период.",
     STATUS_PUBLISHED, "heating_boiler", "Гкал", 3.2),
    ("Вода для полива", "Полив через капельные линии.",
     STATUS_PUBLISHED, "drip_irrigation", "м³", 12.0),
    ("Углекислый газ", "Подкормка повышает интенсивность фотосинтеза.",
     STATUS_PUBLISHED, "co2_system", "кг", 5.5),
    ("Минеральные удобрения", "Питательный раствор подаётся с поливом.",
     STATUS_PUBLISHED, "fertilizers", "кг", 2.8),
    ("Субстрат", "Корнеобитаемая среда вместо грунта.",
     STATUS_PUBLISHED, "substrate", "м³", 1.5),
    # обязательный черновик
    ("Вентиляция", None, STATUS_DRAFT, "default_resource", None, None),
    # обязательная удалённая услуга
    ("Досветка натриевыми лампами", "Устаревшая технология.",
     STATUS_DELETED, "hps_lamp", "кВт·ч", 70.0),
]

SEED_LIKES = [
    (1, 1), (2, 1), (1, 2), (3, 2), (4, 2), (2, 3),
    (3, 4), (1, 5), (4, 6), (2, 7),
]


def init_database():
    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        if session.query(GreenhouseUser).count() > 0:
            return

        session.add_all([
            GreenhouseUser(user_id=1, login="agronom", full_name="Главный агроном", is_agronomist=1),
            GreenhouseUser(user_id=2, login="chekhovich", full_name="Чехович Ю. Ф."),
            GreenhouseUser(user_id=3, login="planner", full_name="Плановик теплицы"),
            GreenhouseUser(user_id=4, login="engineer", full_name="Инженер-технолог"),
        ])
        session.flush()

        for index, (name, description, status, key, unit, value) in enumerate(SEED_RESOURCES, start=1):
            session.add(GreenhouseResource(
                resource_id=index,
                resource_name=name,
                short_description=description,
                resource_status=status,
                image_url=build_minio_url(f"{key}.jpg"),
                video_url=build_minio_url(f"{key}.mp4"),
                unit=unit,
                min_value=value,
                created_at=datetime.now(),
                published_at=datetime.now() if status == STATUS_PUBLISHED else None,
                creator_id=2,
            ))
        session.flush()

        for user_id, resource_id in SEED_LIKES:
            session.add(ResourceLike(user_id=user_id, resource_id=resource_id))

        session.commit()
    finally:
        session.close()
