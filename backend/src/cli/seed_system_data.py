import asyncio
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from src.common.dependencies import get_config
from src.core.security.passwords import PasswordManager
from src.core.uow import create_sqlalchemy_uow
from src.modules.event.models import EventCategory, EventState, EventType
from src.modules.ticket.models import TicketStatus, TicketType
from src.modules.user.models import User, UserRole

CATEGORIES_POOL = {
    "Музыка": ["Рок и Альтернатива", "Джаз и Блюз", "Электронная музыка", "Классика в соборе", "Поп-хиты"],
    "Театр и Кино": ["Драматические спектакли", "Опера и Балет", "Иммерсивные шоу", "Артхаус показы", "Мюзиклы"],
    "Образование": ["IT-Конференции", "Бизнес-интенсивы", "Лекции по искусству", "Языковые клубы", "Хакатоны"],
    "Спорт": ["Футбольные матчи", "Марафоны и Бег", "Турниры по теннису", "Экстремальный спорт", "Киберспорт"],
    "Развлечения": ["Стендап шоу", "Гастро-фестивали", "Квизы и Настолки", "Ночные маркеты", "Выставки комиксов",
                    "Квесты", "Магические шоу", "Детские праздники", "Пляжные вечеринки", "Городские экскурсии"]
}

EVENT_ADJECTIVES = ["Грандиозный", "Камерный", "Ежегодный", "Международный", "Секретный", "Благотворительный",
                    "Андеграундный", "Юбилейный"]
EVENT_NOUN = ["Фестиваль", "Воркшоп", "Перформанс", "Концерт", "Турнир", "Симпозиум", "Рейв", "Слёт"]

CITIES_POOL = [
    "Москва, Парк Горького", "Санкт-Петербург, Севкабель Порт", "Казань, Кремлевская набережная",
    "Екатеринбург, Ельцин Центр", "Новосибирск, Лофт Квадрат", "Нижний Новгород, Стрелка",
    "Сочи, Олимпийский Парк", "Владивосток, Набережная Цесаревича"
]

TICKET_TYPES_POOL = [
    "Standard Pass", "VIP Box", "Early Bird", "Fan Zone", "Backstage Experience",
    "Student Ticket", "Family Bundle", "Premium Lounge", "Super VIP GOLD", "Group Entry"
]

PRICES_POOL = [250.0, 500.0, 900.0, 1500.0, 2500.0, 4000.0, 5500.0, 7000.0, 10000.0]

FIRST_NAMES = ["Иван", "Анна", "Сергей", "Мария", "Александр", "Елена", "Дмитрий", "Ольга", "Михаил", "Наталья"]
LAST_NAMES = ["Петров", "Иванова", "Смирнов", "Кузнецова", "Попов", "Васильева", "Соколов", "Михайлова"]

config = get_config()
pwd_manager = PasswordManager(algorithm=config.password_algorithm, iterations=config.password_iterations)


async def seed_system_data():
    print("Starting comprehensive data seeding process...")
    uow = create_sqlalchemy_uow()

    async with uow:
        print("Generating 50 dynamic ticket types...")
        ticket_types = []
        used_type_names = set()
        while len(ticket_types) < 50:
            t_name = f"{random.choice(TICKET_TYPES_POOL)} #{random.randint(100, 999)}"
            if t_name not in used_type_names:
                used_type_names.add(t_name)

                async with uow._session.begin_nested():
                    try:
                        t_type = await uow.ticket_type.create(name=t_name)
                        ticket_types.append(t_type)
                    except IntegrityError:
                        pass

        await uow._session.flush()

        orm_ticket_types = []
        for t in ticket_types:
            if t is not None and hasattr(t, "id"):
                fetched = await uow._session.get(TicketType, t.id)
                if fetched:
                    orm_ticket_types.append(fetched)

        if not orm_ticket_types:
            res = await uow._session.execute(select(TicketType).limit(50))
            orm_ticket_types = list(res.scalars().all())

        print("Generating user base with ticket type permissions...")
        allowed_event_hosts = []
        hashed_password = pwd_manager.hash_password("TestPass123!")

        # Загружаем админа сразу с жадной загрузкой ticket_types
        res = await uow._session.execute(
            select(User).where(User.email == "admin@test.ru").options(selectinload(User.ticket_types))
        )
        admin_obj = res.scalar_one_or_none()

        if admin_obj is None:
            async with uow._session.begin_nested():
                try:
                    admin_dto = await uow.user.create(
                        email="admin@test.ru",
                        username="system_admin",
                        password=hashed_password,
                        role=UserRole.ADMIN,
                        is_active=True
                    )
                    await uow._session.flush()

                    res = await uow._session.execute(
                        select(User).where(User.id == admin_dto.id).options(selectinload(User.ticket_types))
                    )
                    admin_obj = res.scalar_one_or_none()
                except IntegrityError:
                    res = await uow._session.execute(
                        select(User).where(User.email == "admin@test.ru").options(selectinload(User.ticket_types))
                    )
                    admin_obj = res.scalar_one_or_none()

        if admin_obj is not None:
            if orm_ticket_types and not admin_obj.ticket_types:
                admin_obj.ticket_types.extend(random.sample(orm_ticket_types, k=min(15, len(orm_ticket_types))))
            allowed_event_hosts.append((admin_obj.id, admin_obj.ticket_types))

        for i in range(1, 11):
            f_name = random.choice(FIRST_NAMES)
            l_name = random.choice(LAST_NAMES)
            username = f"{f_name.lower()}_{l_name.lower()}_{random.randint(10, 99)}"
            email = f"{username}@test.ru"
            role = random.choice([UserRole.VERIFIED_USER, UserRole.MODERATOR, UserRole.USER])

            async with uow._session.begin_nested():
                try:
                    user_dto = await uow.user.create(
                        email=email,
                        username=username,
                        password=hashed_password,
                        role=role,
                        is_active=True
                    )
                    await uow._session.flush()

                    res = await uow._session.execute(
                        select(User).where(User.id == user_dto.id).options(selectinload(User.ticket_types))
                    )
                    user_obj = res.scalar_one_or_none()

                    if user_obj:
                        user_obj.ticket_types.extend(random.sample(orm_ticket_types, k=min(10, len(orm_ticket_types))))
                        if role in [UserRole.VERIFIED_USER, UserRole.ADMIN]:
                            allowed_event_hosts.append((user_obj.id, user_obj.ticket_types))
                except IntegrityError:
                    pass

        await uow._session.flush()
        print("Generating 50 specialized event categories...")
        category_ids = []
        for root_name, subs in CATEGORIES_POOL.items():
            root_cat = None

            res = await uow._session.execute(select(EventCategory).where(EventCategory.name == f"{root_name} (Seed)"))
            root_cat = res.scalar_one_or_none()

            if root_cat is None:
                async with uow._session.begin_nested():
                    try:
                        root_cat = await uow.event_category.create(
                            name=f"{root_name} (Seed)",
                            parent_id=None
                        )
                        await uow._session.flush()
                    except IntegrityError:
                        res = await uow._session.execute(
                            select(EventCategory).where(EventCategory.name == f"{root_name} (Seed)"))
                        root_cat = res.scalar_one_or_none()

            for sub_name in subs:
                res = await uow._session.execute(
                    select(EventCategory).where(EventCategory.name == f"{sub_name} (Seed)"))
                sub_cat = res.scalar_one_or_none()

                if sub_cat is None:
                    async with uow._session.begin_nested():
                        try:
                            sub_cat = await uow.event_category.create(
                                name=f"{sub_name} (Seed)",
                                parent_id=root_cat.id if root_cat else None
                            )
                            await uow._session.flush()
                            category_ids.append(sub_cat.id)
                        except IntegrityError:
                            res = await uow._session.execute(
                                select(EventCategory).where(EventCategory.name == f"{sub_name} (Seed)"))
                            sub_cat = res.scalar_one_or_none()
                            if sub_cat:
                                category_ids.append(sub_cat.id)
                else:
                    category_ids.append(sub_cat.id)

        if not category_ids:
            res = await uow._session.execute(select(EventCategory.id).where(EventCategory.parent_id.is_not(None)))
            category_ids = list(res.scalars().all())

        print("Generating 100 highly realistic events...")
        event_ids = []
        for i in range(1, 101):
            title = f"{random.choice(EVENT_ADJECTIVES)} {random.choice(EVENT_NOUN)} {random.randint(2026, 2027)}"
            description = f"Добро пожаловать на '{title}'! Вас ждет уникальная программа."

            e_type = random.choice([EventType.OFFLINE, EventType.ONLINE])
            address = random.choice(CITIES_POOL) if e_type == EventType.OFFLINE else None
            future_date = datetime.now(timezone.utc) + timedelta(days=random.randint(10, 365))

            host_user_id, host_ticket_types = random.choice(allowed_event_hosts) if allowed_event_hosts else (
            1, orm_ticket_types)

            async with uow._session.begin_nested():
                try:
                    event = await uow.event.create(
                        title=title,
                        description=description,
                        category_id=random.choice(category_ids) if category_ids else 1,
                        user_id=host_user_id,
                        state=EventState.APPROVED,
                        event_type=e_type,
                        address=address,
                        event_date=future_date
                    )
                    await uow._session.flush()
                    event_ids.append((event.id, host_ticket_types))
                except IntegrityError:
                    pass

        print("Generating 1000 balanced tickets...")
        tickets_created = 0

        if event_ids:
            for event_id, host_allowed_types in event_ids:
                num_types_for_event = min(random.randint(2, 5), len(host_allowed_types))
                if num_types_for_event == 0:
                    host_allowed_types = orm_ticket_types
                    num_types_for_event = random.randint(2, 5)

                local_types = random.sample(host_allowed_types, k=num_types_for_event)
                tickets_per_type = 1000 // (100 * num_types_for_event)
                if tickets_per_type == 0:
                    tickets_per_type = 1

                for t_type in local_types:
                    base_price = random.choice(PRICES_POOL)

                    for _ in range(tickets_per_type):
                        if tickets_created >= 1000:
                            break

                        await uow.ticket.create(
                            event_id=event_id,
                            type_id=t_type.id,
                            price=base_price,
                            status=TicketStatus.AVAILABLE,
                            user_id=None,
                            anonymous_email=None
                        )
                        tickets_created += 1

            if tickets_created < 1000:
                remainder = 1000 - tickets_created
                print(f"Adding {remainder} remainder tickets for balance...")
                for _ in range(remainder):
                    chosen_event_id, chosen_host_types = random.choice(event_ids)
                    chosen_type = random.choice(chosen_host_types) if chosen_host_types else random.choice(
                        orm_ticket_types)

                    await uow.ticket.create(
                        event_id=chosen_event_id,
                        type_id=chosen_type.id,
                        price=1500.0,
                        status=TicketStatus.AVAILABLE,
                        user_id=None,
                        anonymous_email=None
                    )
                    tickets_created += 1

        await uow.commit()

    print("\n[SUCCESS] Highly diversified environment is ready!")
    print(f"-> Created/Skipped structural categories: 50")
    print(f"-> Created/Skipped unique ticket types: 50")
    print(f"-> Processed upcoming events: {len(event_ids)}")
    print(f"-> Total exact tickets available added: {tickets_created}")


if __name__ == "__main__":
    asyncio.run(seed_system_data())
