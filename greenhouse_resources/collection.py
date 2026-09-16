"""
Модель-коллекция ресурсов для выращивания урожая в теплице на Севере.
В первой лабораторной база данных не используется — все данные берутся
прямо из этой коллекции.
"""

MINIO_BASE_URL = "http://localhost:9000/greenhouse"

STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
STATUS_DELETED = "deleted"

STATUS_TITLES = {
    STATUS_DRAFT: "Черновик",
    STATUS_PUBLISHED: "Опубликован",
    STATUS_DELETED: "Удалён",
}

# Массив услуг с вложенными лайками (ID пользователей).
# image_key и video_key — два отдельных поля с ключами файлов в Minio.
GREENHOUSE_RESOURCES = [
    {
        "resource_id": 1,
        "resource_name": "Площадь теплицы",
        "equipment": "Теплица «Воля Богатырь», поликарбонат 4 мм",
        "unit": "м²",
        "min_value": 8.0,
        "short_description": (
            "Полезная площадь под посадку. Зависит от схемы размещения "
            "растений и ширины технологических проходов."
        ),
        "status": STATUS_PUBLISHED,
        "image_key": "greenhouse_frame.jpg",
        "video_key": "greenhouse_frame.mp4",
        "liked_by": [1, 2, 4],
    },
    {
        "resource_id": 2,
        "resource_name": "Электроэнергия",
        "equipment": "Фитооблучатели Philips GreenPower LED",
        "unit": "кВт·ч",
        "min_value": 45.0,
        "short_description": (
            "Досветка растений в период короткого светового дня. Расход "
            "зависит от мощности облучателей и длительности досветки."
        ),
        "status": STATUS_PUBLISHED,
        "image_key": "led_lighting.jpg",
        "video_key": "led_lighting.mp4",
        "liked_by": [1, 3, 5, 6, 7, 8, 9, 10, 11, 12],
    },
    {
        "resource_id": 3,
        "resource_name": "Тепловая энергия",
        "equipment": "Газовый котёл Viessmann Vitoplex 100",
        "unit": "Гкал",
        "min_value": 3.2,
        "short_description": (
            "Обогрев теплицы в зимний период. На Севере разница температур "
            "внутри и снаружи достигает 50 °C."
        ),
        "status": STATUS_PUBLISHED,
        "image_key": "heating_boiler.jpg",
        "video_key": "heating_boiler.mp4",
        "liked_by": [2, 3, 7, 9],
    },
    {
        "resource_id": 4,
        "resource_name": "Вода для полива",
        "equipment": "Капельная система Netafim",
        "unit": "м³",
        "min_value": 12.0,
        "short_description": (
            "Полив через капельные линии. Норма зависит от культуры, "
            "фазы вегетации и типа субстрата."
        ),
        "status": STATUS_PUBLISHED,
        "image_key": "drip_irrigation.jpg",
        "video_key": "drip_irrigation.mp4",
        "liked_by": [4, 5, 8],
    },
    {
        "resource_id": 5,
        "resource_name": "Углекислый газ",
        "equipment": "Система дозирования Priva CO2",
        "unit": "кг",
        "min_value": 5.5,
        "short_description": (
            "Подкормка углекислым газом повышает интенсивность фотосинтеза "
            "при закрытых форточках."
        ),
        "status": STATUS_PUBLISHED,
        "image_key": "co2_system.jpg",
        "video_key": "co2_system.mp4",
        "liked_by": [1, 6],
    },
    {
        "resource_id": 6,
        "resource_name": "Минеральные удобрения",
        "equipment": "Водорастворимые удобрения Yara",
        "unit": "кг",
        "min_value": 2.8,
        "short_description": (
            "Питательный раствор подаётся вместе с поливом. Состав "
            "корректируется по фазе развития растения."
        ),
        "status": STATUS_PUBLISHED,
        "image_key": "fertilizers.jpg",
        "video_key": "fertilizers.mp4",
        "liked_by": [3, 7, 10],
    },
    {
        "resource_id": 7,
        "resource_name": "Субстрат",
        "equipment": "Минеральная вата Grodan",
        "unit": "м³",
        "min_value": 1.5,
        "short_description": (
            "Корнеобитаемая среда вместо грунта. Заменяется каждый "
            "производственный цикл."
        ),
        "status": STATUS_PUBLISHED,
        "image_key": "substrate.jpg",
        "video_key": "substrate.mp4",
        "liked_by": [2, 11],
    },
    # Единственная услуга в статусе черновик — отображается на странице «Добавление»
    {
        "resource_id": 8,
        "resource_name": "Вентиляция",
        "equipment": "Приточные установки Priva",
        "unit": "м³/ч",
        "min_value": 0.0,
        "short_description": "",
        "status": STATUS_DRAFT,
        "image_key": "",
        "video_key": "",
        "liked_by": [],
    },
    # Удалённая услуга — нигде в интерфейсе не отображается
    {
        "resource_id": 9,
        "resource_name": "Досветка натриевыми лампами",
        "equipment": "ДНаТ 600 Вт",
        "unit": "кВт·ч",
        "min_value": 70.0,
        "short_description": "Устаревшая технология досветки.",
        "status": STATUS_DELETED,
        "image_key": "hps_lamp.jpg",
        "video_key": "hps_lamp.mp4",
        "liked_by": [1],
    },
]


def build_minio_url(file_key):
    """Собирает полный url файла в Minio по ключу на латинице."""
    if not file_key:
        return ""
    return f"{MINIO_BASE_URL}/{file_key}"


def count_likes(resource):
    """Количество лайков вычисляется по коллекции в контроллере-обработчике."""
    return len(resource["liked_by"])


def get_published_resources(min_value=None):
    """Опубликованные ресурсы с фильтрацией по минимальному значению."""
    found = [r for r in GREENHOUSE_RESOURCES if r["status"] == STATUS_PUBLISHED]
    if min_value is not None:
        found = [r for r in found if r["min_value"] >= min_value]
    return found


def get_resource_by_id(resource_id):
    """Одна услуга по идентификатору. Удалённые не отдаются."""
    for resource in GREENHOUSE_RESOURCES:
        if resource["resource_id"] == resource_id and resource["status"] != STATUS_DELETED:
            return resource
    return None


def get_next_published(resource_id):
    """Следующая опубликованная услуга после указанной. По кругу."""
    published = get_published_resources()
    if not published:
        return None
    for position, resource in enumerate(published):
        if resource["resource_id"] == resource_id:
            return published[(position + 1) % len(published)]
    return published[0]


def get_draft_resource():
    """Единственная услуга в статусе черновик."""
    for resource in GREENHOUSE_RESOURCES:
        if resource["status"] == STATUS_DRAFT:
            return resource
    return None


def get_min_value_bounds():
    """Границы слайдера фильтрации считаются по коллекции."""
    values = [r["min_value"] for r in get_published_resources()]
    if not values:
        return 0.0, 100.0
    return min(values), max(values)
