"""Наполнение таблиц начальными данными.
Сами таблицы создаются миграциями Alembic: alembic upgrade head"""

import hashlib
from datetime import datetime

from greenhouse_resources.models import (
    GreenhouseResource, GreenhouseUser, ResourceLike, SessionLocal,
    STATUS_DELETED, STATUS_DRAFT, STATUS_PUBLISHED, build_minio_url,
)

SEED_RESOURCES = [
    ("Площадь теплицы", "Полезная площадь под посадку. Зависит от схемы "
     "размещения растений и ширины технологических проходов.",
     STATUS_PUBLISHED, "greenhouse_frame", "м²", 8.0),
    ("Электроэнергия", "Досветка растений в период короткого светового дня. "
     "Расход зависит от мощности облучателей и длительности досветки.",
     STATUS_PUBLISHED, "led_lighting", "кВт·ч", 45.0),
    ("Тепловая энергия", "Обогрев теплицы в зимний период. На Севере разница "
     "температур внутри и снаружи достигает 50 °C.",
     STATUS_PUBLISHED, "heating_boiler", "Гкал", 3.2),
    ("Вода для полива", "Полив через капельные линии. Норма зависит от культуры, "
     "фазы вегетации и типа субстрата.",
     STATUS_PUBLISHED, "drip_irrigation", "м³", 12.0),
    ("Углекислый газ", "Подкормка углекислым газом повышает интенсивность "
     "фотосинтеза при закрытых форточках.",
     STATUS_PUBLISHED, "co2_system", "кг", 5.5),
    ("Минеральные удобрения", "Питательный раствор подаётся вместе с поливом. "
     "Состав корректируется по фазе развития растения.",
     STATUS_PUBLISHED, "fertilizers", "кг", 2.8),
    ("Субстрат", "Корнеобитаемая среда вместо грунта. Заменяется каждый "
     "производственный цикл.",
     STATUS_PUBLISHED, "substrate", "м³", 1.5),
    # обязательный черновик: файлов в Minio нет — показываются файлы по умолчанию
    ("Вентиляция", None, STATUS_DRAFT, "ventilation_draft", None, None),
    # обязательная удалённая услуга
    ("Досветка натриевыми лампами", "Устаревшая технология досветки.",
     STATUS_DELETED, "hps_lamp", "кВт·ч", 70.0),
]

SEED_LIKES = [
    (1, 1), (2, 1), (1, 2), (3, 2), (4, 2), (2, 3),
    (3, 4), (1, 5), (4, 6), (2, 7),
]


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_database():
    session = SessionLocal()
    try:
        if session.query(GreenhouseUser).count() > 0:
            return

        # ид назначаются последовательностью: 1..4 в порядке добавления
        for login in ("agronom", "chekhovich", "planner", "engineer"):
            session.add(GreenhouseUser(login=login, password=hash_password(f"{login}123")))
            session.flush()

        for name, description, status, key, unit, value in SEED_RESOURCES:
            session.add(GreenhouseResource(
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
