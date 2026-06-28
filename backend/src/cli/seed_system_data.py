import asyncio
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.app.uow import create_app_uow
from src.core.security.passwords import PasswordManager
from src.core.settings import get_settings

from src.modules.user.models import User, UserRole
from src.modules.event.models import EventCategory, Event, EventType, EventState
from src.modules.ticket.models import TicketCategory, Ticket, TicketStatus
from src.modules.order.models import Order, OrderItem, OrderStatus
from src.modules.views.models import ViewLog

CATEGORIES_POOL = {
    "Музыка": ["Рок и Альтернатива", "Джаз и Блюз", "Электронная музыка", "Классика в соборе", "Поп-хиты"],
    "Театр и Кино": ["Драматические спектакли", "Опера и Балет", "Иммерсивные шоу", "Артхаус показы", "Мюзиклы"],
    "Образование": ["IT-Конференции", "Бизнес-интенсивы", "Лекции по искусству", "Языковые клубы", "Хакатоны"],
    "Спорт": ["Футбольные матчи", "Марафоны и Бег", "Турниры по теннису", "Экстремальный спорт", "Киберспорт"],
    "Развлечения": ["Стендап шоу", "Гастро-фестивали", "Квизы и Настолки", "Ночные маркеты", "Выставки комиксов"]
}

EVENT_ADJECTIVES = ["Грандиозный", "Камерный", "Ежегодный", "Международный", "Секретный", "Благотворительный", "Юбилейный"]
EVENT_NOUNS = ["Фестиваль", "Воркшоп", "Перформанс", "Концерт", "Турнир", "Симпозиум", "Рейв", "Слёт"]

CITIES_POOL = [
    "Москва, Парк Горького", "Санкт-Петербург, Севкабель Порт", "Казань, Кремлевская набережная",
    "Екатеринбург, Ельцин Центр", "Новосибирск, Лофт Квадрат", "Сочи, Олимпийский Парк"
]

TICKET_NAMES_POOL = ["Standard Pass", "VIP Box", "Early Bird", "Fan Zone", "Student Ticket"]
PRICES_POOL = [490.0, 1500.0, 2900.0, 5500.0, 9900.0]

FIRST_NAMES = ["Иван", "Анна", "Сергей", "Мария", "Александр", "Елена", "Дмитрий", "Ольга"]
LAST_NAMES = ["Петров", "Иванова", "Смирнов", "Кузнецова", "Попов", "Васильева"]

config = get_settings()
pwd_manager = PasswordManager(algorithm=config.password_algorithm, iterations=config.password_iterations)


async def seed_system_data():
    print("[   0% ] Initializing database unit of work...")
    uow = create_app_uow()

    async with uow:
        print("[  10% ] Seeding users and roles...")
        allowed_event_hosts = []
        regular_buyers = []
        all_user_ids = []

        admin_raw_password = "".join(
            random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$", k=14))
        admin_hashed_password = pwd_manager.hash_password(admin_raw_password)

        res = await uow._session.execute(select(User).where(User.email == "admin@test.ru"))
        admin_obj = res.scalar_one_or_none()

        if admin_obj is None:
            admin_obj = await uow.user.create(
                email="admin@test.ru",
                username="system_admin",
                password=admin_hashed_password,
                role=UserRole.ADMIN,
                is_active=True
            )
            await uow._session.flush()
            print(f"[ADMIN CREATED] Email: admin@test.ru | Password: {admin_raw_password}")
        allowed_event_hosts.append(admin_obj.id)
        all_user_ids.append(admin_obj.id)

        print("-" * 80)
        print(f"{'ROLE':<18} | {'EMAIL':<30} | {'RAW PASSWORD'}")
        print("-" * 80)

        for i in range(1, 35):
            f_name = random.choice(FIRST_NAMES)
            l_name = random.choice(LAST_NAMES)
            username = f"{f_name.lower()}_{l_name.lower()}_{random.randint(10, 99)}"
            email = f"{username}@test.ru"
            role = random.choice([UserRole.USER, UserRole.VERIFIED_USER, UserRole.ON_VERIFICATION, UserRole.MODERATOR])

            raw_password = "".join(
                random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$", k=12))
            hashed_password = pwd_manager.hash_password(raw_password)

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

                    if user_dto is not None:
                        all_user_ids.append(user_dto.id)
                        print(f"{role.value:<18} | {email:<30} | {raw_password}")

                        if role in [UserRole.VERIFIED_USER, UserRole.MODERATOR]:
                            allowed_event_hosts.append(user_dto.id)
                        elif role == UserRole.USER:
                            regular_buyers.append(user_dto.id)
                except IntegrityError:
                    pass

        print("-" * 80)
        print(f"[  25% ] Total users registered: {len(all_user_ids)}. Seeding event categories hierarchy...")
        leaf_category_ids = []
        for root_name, subs in CATEGORIES_POOL.items():
            res = await uow._session.execute(select(EventCategory).where(EventCategory.name == root_name))
            root_cat = res.scalar_one_or_none()

            if root_cat is None:
                root_cat = await uow.event_category.create(name=root_name, parent_id=None)
                await uow._session.flush()

            for sub_name in subs:
                res = await uow._session.execute(select(EventCategory).where(EventCategory.name == sub_name))
                sub_cat = res.scalar_one_or_none()

                if sub_cat is None:
                    async with uow._session.begin_nested():
                        try:
                            sub_cat = await uow.event_category.create(name=sub_name, parent_id=root_cat.id)
                            await uow._session.flush()
                            leaf_category_ids.append(sub_cat.id)
                        except IntegrityError:
                            pass
                else:
                    leaf_category_ids.append(sub_cat.id)

        print("[  40% ] Generating 100 historical and upcoming events with ticket categories...")
        purchasable_ticket_categories = []
        all_event_ids = []
        now_utc = datetime.now(timezone.utc)
        event_model_name = uow.event.get_model_name()

        for i in range(1, 101):
            title = f"{random.choice(EVENT_ADJECTIVES)} {random.choice(EVENT_NOUNS)} {random.randint(2026, 2027)}"
            description = f"Приглашаем вас на мероприятие '{title}'. Проведи время незабываемо!"
            e_type = random.choice([EventType.OFFLINE, EventType.ONLINE])
            address = random.choice(CITIES_POOL) if e_type == EventType.OFFLINE else None

            if i <= 20:
                event_date = now_utc - timedelta(days=random.randint(2, 45))
                state = EventState.APPROVED
            else:
                event_date = now_utc + timedelta(days=random.randint(10, 200))
                state = random.choice([EventState.APPROVED, EventState.DRAFT, EventState.ON_MODERATION])

            event_obj = await uow.event.create(
                title=title,
                description=description,
                user_id=random.choice(allowed_event_hosts),
                category_id=random.choice(leaf_category_ids),
                state=state,
                event_type=e_type,
                address=address,
                event_date=event_date
            )
            await uow._session.flush()
            all_event_ids.append(event_obj.id)

            available_ticket_names = random.sample(TICKET_NAMES_POOL, k=random.randint(1, 3))
            for t_idx, ticket_name in enumerate(available_ticket_names):
                ticket_cat = await uow.ticket_category.create(
                    event_id=event_obj.id,
                    name=ticket_name,
                    price=PRICES_POOL[t_idx % len(PRICES_POOL)],
                    total_quantity=random.randint(40, 300)
                )
                await uow._session.flush()

                if state == EventState.APPROVED:
                    purchasable_ticket_categories.append(ticket_cat)

            if i % 25 == 0:
                print(f"[  55% ] Processed {i}/100 events...")
        print("[  60% ] Processing 150 customer orders and ticket emissions...")
        if purchasable_ticket_categories:
            for o_idx in range(1, 151):
                is_anon_purchase = random.random() < 0.25

                if is_anon_purchase:
                    buyer_user_id = None
                    anonymous_email = f"guest_{random.randint(10000, 99999)}@example.com"
                else:
                    buyer_user_id = random.choice(regular_buyers) if regular_buyers else admin_obj.id
                    anonymous_email = None

                order_status = random.choice([OrderStatus.PAID, OrderStatus.PENDING, OrderStatus.CANCELLED])
                target_cat = random.choice(purchasable_ticket_categories)
                ticket_qty = random.randint(1, 3)

                order_items_data = [{"category_id": target_cat.id, "quantity": ticket_qty}]

                order_dto = await uow.order.create(
                    user_id=buyer_user_id,
                    anonymous_email=anonymous_email,
                    order_items=order_items_data
                )
                await uow._session.flush()

                if order_status == OrderStatus.PAID:
                    await uow.order.mark_as_paid(order_dto.id)
                elif order_status == OrderStatus.CANCELLED:
                    await uow.order.cancel_if_not_paid(order_dto.id)

                if o_idx % 50 == 0:
                    print(f"[  75% ] Processed {o_idx}/150 orders...")

        print("[  80% ] Seeding unique event view logs...")
        processed_views = 0
        for event_id in all_event_ids:
            viewers = random.sample(all_user_ids, k=random.randint(5, min(15, len(all_user_ids))))

            if random.random() < 0.7:
                await uow.view_logs.create_view_log(
                    table_name=event_model_name,
                    obj_id=event_id,
                    user_id=None
                )

            if viewers:
                await uow.view_logs.bulk_create_view_logs(
                    table_name=event_model_name,
                    obj_ids=[event_id],
                    user_id=random.choice(viewers)
                )

            for viewer_id in viewers:
                async with uow._session.begin_nested():
                    try:
                        await uow.view_logs.create_view_log(
                            table_name=event_model_name,
                            obj_id=event_id,
                            user_id=viewer_id
                        )
                    except IntegrityError:
                        pass

            processed_views += 1
            if processed_views % 25 == 0:
                print(f"[  90% ] Logged view metrics for {processed_views}/100 events...")

        print("[  95% ] Committing transaction changes to database...")
        await uow.commit()
        print("[ 100% ] Database seeding completed successfully.")


async def main():
    print("[ START ] Starting async system data seed script...")
    start_time = datetime.now(timezone.utc)
    try:
        await seed_system_data()
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        print(f"[ FINISH ] Done. Execution time: {duration:.2f} seconds.")
    except Exception as e:
        print(f"[ CRITICAL ] Seed failed with exception: {e}")
        raise e


if __name__ == "__main__":
    asyncio.run(main())
