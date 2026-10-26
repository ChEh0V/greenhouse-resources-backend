"""Наполнение таблиц начальными данными.
Сами таблицы создаются миграциями Alembic: alembic upgrade head"""

from datetime import datetime

from greenhouse_resources.minio_storage import build_minio_url
from greenhouse_resources.models import (
    GreenhouseResource, GreenhouseUser, ResourceAttribute, ResourceAttributeValue, ResourceLike,
    SessionLocal,
    STATUS_DELETED, STATUS_DRAFT, STATUS_PUBLISHED,
)
from greenhouse_resources.security import hash_password

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
    # обязательный черновик — у пользователя planner, чтобы создатель (chekhovich)
    # мог добавить новый ресурс: у пользователя не более одного черновика
    ("Вентиляция", None, STATUS_DRAFT, "ventilation_draft", None, None),
    # обязательная удалённая услуга
    ("Досветка натриевыми лампами", "Устаревшая технология досветки.",
     STATUS_DELETED, "hps_lamp", "кВт·ч", 70.0),
]

SEED_LIKES = [
    (1, 1), (2, 1), (1, 2), (3, 2), (4, 2), (2, 3),
    (3, 4), (1, 5), (4, 6), (2, 7),
]

# Дополнительные характеристики ресурсов (вертикальная таблица атрибутов).
# У каждого ресурса свой набор: незаполненные атрибуты просто отсутствуют.
SEED_ATTRIBUTES = ["Оборудование", "Производитель", "Срок службы", "Норма на 1 м² теплицы"]
SEED_ATTRIBUTE_VALUES = {
    1: {"Оборудование": "Теплица из поликарбоната 4 мм", "Производитель": "Воля",
        "Срок службы": "15 лет"},
    2: {"Оборудование": "Фитооблучатели LED", "Производитель": "Philips GreenPower",
        "Срок службы": "35 000 ч", "Норма на 1 м² теплицы": "0,25 кВт·ч в сутки"},
    3: {"Оборудование": "Газовый котёл", "Производитель": "Viessmann Vitoplex 100",
        "Срок службы": "20 лет"},
    4: {"Оборудование": "Капельная система полива", "Производитель": "Netafim",
        "Норма на 1 м² теплицы": "4 л в сутки"},
    5: {"Оборудование": "Система дозирования CO2", "Производитель": "Priva",
        "Норма на 1 м² теплицы": "0,8 г в час"},
    6: {"Оборудование": "Водорастворимые удобрения", "Производитель": "Yara"},
    7: {"Оборудование": "Минеральная вата", "Производитель": "Grodan", "Срок службы": "1 сезон"},
}


def init_attributes(session):
    """Атрибуты добавляются отдельно, чтобы появиться и в уже заполненной базе."""
    if session.query(ResourceAttribute).count() > 0:
        return
    ids = {}
    for name in SEED_ATTRIBUTES:
        attribute = ResourceAttribute(attribute_name=name)
        session.add(attribute)
        session.flush()
        ids[name] = attribute.attribute_id
    for resource_id, values in SEED_ATTRIBUTE_VALUES.items():
        if session.get(GreenhouseResource, resource_id) is None:
            continue
        for name, value in values.items():
            session.add(ResourceAttributeValue(resource_id=resource_id, attribute_id=ids[name],
                                               attribute_value=value))
    session.commit()


def init_database():
    session = SessionLocal()
    try:
        if session.query(GreenhouseUser).count() > 0:
            init_attributes(session)
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
                creator_id=3 if status == STATUS_DRAFT else 2,
            ))
            session.flush()

        for user_id, resource_id in SEED_LIKES:
            session.add(ResourceLike(user_id=user_id, resource_id=resource_id))

        session.commit()
        init_attributes(session)
    finally:
        session.close()
