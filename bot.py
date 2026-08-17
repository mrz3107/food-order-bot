import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

from config import BOT_TOKEN
from api_client import get_menu, create_order, get_order


logging.basicConfig(level=logging.INFO)

router = Router()

carts = {}
user_orders = {}


class OrderForm(StatesGroup):
    name = State()
    phone = State()
    address = State()


def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🍽 Menyu"),
                KeyboardButton(text="🛒 Savat"),
            ],
            [
                KeyboardButton(text="📦 Buyurtmalarim"),
            ],
        ],
        resize_keyboard=True,
    )


def menu_item_kb(item_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Savatga qo'shish",
                    callback_data=f"add:{item_id}",
                )
            ]
        ]
    )


def cart_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Buyurtma berish",
                    callback_data="checkout",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Savatni tozalash",
                    callback_data="clear_cart",
                )
            ],
        ]
    )


def confirm_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data="confirm_order",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="cancel_order",
                )
            ],
        ]
    )


@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    carts.setdefault(user_id, {})

    await message.answer(
        "Assalomu alaykum! 🍔 Ovqat buyurtma botiga xush kelibsiz.",
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "🍽 Menyu")
async def show_menu(message: Message):
    items = await get_menu()

    if not items:
        await message.answer("❌ Menyuni olishda xatolik yoki menyu bo'sh.")
        return

    await message.answer("🍽 <b>Bizning menyu:</b>", parse_mode="HTML")

    for item in items:
        if not item.get("available", True):
            continue

        item_id = item.get("id")
        name = item.get("name", "Noma'lum")
        description = item.get("description") or ""
        price = item.get("price", 0)

        text = (
            f"<b>{name}</b>\n"
            f"{description}\n"
            f"💰 {price:,.0f} so'm"
        )

        await message.answer(
            text,
            reply_markup=menu_item_kb(item_id),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("add:"))
async def add_to_cart(callback: CallbackQuery):
    try:
        item_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Mahsulot xatosi", show_alert=True)
        return

    user_id = callback.from_user.id

    cart = carts.setdefault(user_id, {})
    cart[item_id] = cart.get(item_id, 0) + 1

    await callback.answer(
        "Savatga qo'shildi ✅"
    )


@router.message(F.text == "🛒 Savat")
async def show_cart(message: Message):
    user_id = message.from_user.id
    cart = carts.get(user_id, {})

    if not cart:
        await message.answer(
            "🛒 Savatingiz bo'sh.\n\n"
            "Avval menyudan taom tanlang 🍽",
            reply_markup=main_menu_kb(),
        )
        return

    items = await get_menu()

    if not items:
        await message.answer(
            "❌ Menyuni olishda xatolik."
        )
        return

    menu_dict = {
        int(item["id"]): item
        for item in items
    }

    lines = []
    total = 0

    for item_id, quantity in cart.items():
        item = menu_dict.get(int(item_id))

        if not item:
            continue

        price = float(item.get("price", 0))
        subtotal = price * quantity
        total += subtotal

        lines.append(
            f"🍽 {item['name']} x{quantity} = {subtotal:,.0f} so'm"
        )

    if not lines:
        await message.answer(
            "❌ Savatdagi mahsulotlarni topib bo'lmadi."
        )
        return

    text = (
        "🛒 <b>Sizning savatingiz:</b>\n\n"
        + "\n".join(lines)
        + f"\n\n💵 <b>Jami: {total:,.0f} so'm</b>"
    )

    await message.answer(
        text,
        reply_markup=cart_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    carts[user_id] = {}

    await callback.answer("Savat tozalandi 🗑")

    await callback.message.answer(
        "🗑 Savat tozalandi.",
        reply_markup=main_menu_kb(),
    )


@router.callback_query(F.data == "checkout")
async def start_checkout(
    callback: CallbackQuery,
    state: FSMContext,
):
    user_id = callback.from_user.id
    cart = carts.get(user_id, {})

    if not cart:
        await callback.answer(
            "Savat bo'sh!",
            show_alert=True,
        )
        return

    await callback.answer()

    await callback.message.answer(
        "👤 Ismingizni kiriting:",
        reply_markup=ReplyKeyboardRemove(),
    )

    await state.set_state(OrderForm.name)


@router.message(OrderForm.name)
async def process_name(
    message: Message,
    state: FSMContext,
):
    name = (message.text or "").strip()

    if not name:
        await message.answer("❌ Ismingizni kiriting.")
        return

    await state.update_data(name=name)

    await message.answer(
        "📞 Telefon raqamingizni kiriting:\n"
        "Masalan: +998901234567"
    )

    await state.set_state(OrderForm.phone)


@router.message(OrderForm.phone)
async def process_phone(
    message: Message,
    state: FSMContext,
):
    phone = (message.text or "").strip()

    if not phone:
        await message.answer("❌ Telefon raqamingizni kiriting.")
        return

    await state.update_data(phone=phone)

    await message.answer(
        "📍 Yetkazib berish manzilingizni kiriting:"
    )

    await state.set_state(OrderForm.address)


@router.message(OrderForm.address)
async def process_address(
    message: Message,
    state: FSMContext,
):
    address = (message.text or "").strip()

    if not address:
        await message.answer("❌ Manzilni kiriting.")
        return

    await state.update_data(address=address)

    data = await state.get_data()

    user_id = message.from_user.id
    cart = carts.get(user_id, {})

    if not cart:
        await message.answer(
            "❌ Savat bo'sh.",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        return

    items = await get_menu()

    if not items:
        await message.answer(
            "❌ Menyuni olishda xatolik."
        )
        await state.clear()
        return

    menu_dict = {
        int(item["id"]): item
        for item in items
    }

    lines = []
    total = 0

    for item_id, quantity in cart.items():
        item = menu_dict.get(int(item_id))

        if not item:
            continue

        price = float(item.get("price", 0))
        subtotal = price * quantity
        total += subtotal

        lines.append(
            f"🍽 {item['name']} x{quantity} = {subtotal:,.0f} so'm"
        )

    if not lines:
        await message.answer(
            "❌ Savatdagi mahsulotlar topilmadi."
        )
        await state.clear()
        return

    text = (
        "📋 <b>Buyurtmangizni tasdiqlang:</b>\n\n"
        f"👤 Ism: {data['name']}\n"
        f"📞 Tel: {data['phone']}\n"
        f"📍 Manzil: {data['address']}\n\n"
        + "\n".join(lines)
        + f"\n\n💵 <b>Jami: {total:,.0f} so'm</b>"
    )

    await message.answer(
        text,
        reply_markup=confirm_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "confirm_order")
async def confirm_order(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()

    name = data.get("name")
    phone = data.get("phone")
    address = data.get("address")

    if not name or not phone or not address:
        await callback.answer(
            "❌ Buyurtma ma'lumotlari to'liq emas!",
            show_alert=True,
        )

        await state.clear()

        await callback.message.answer(
            "Buyurtmani boshidan boshlang.",
            reply_markup=main_menu_kb(),
        )
        return

    user_id = callback.from_user.id
    cart = carts.get(user_id, {})

    if not cart:
        await callback.answer(
            "Savat bo'sh!",
            show_alert=True,
        )

        await state.clear()
        return

    items_payload = [
        {
            "menu_item_id": int(item_id),
            "quantity": int(quantity),
        }
        for item_id, quantity in cart.items()
    ]

    try:
        status, result = await create_order(
            customer_name=name,
            customer_phone=phone,
            address=address,
            items=items_payload,
        )
    except Exception as e:
        logging.exception("CREATE ORDER ERROR")

        await callback.answer()

        await callback.message.answer(
            f"❌ Server bilan bog'lanishda xatolik:\n{e}"
        )

        await state.clear()
        return

    await callback.answer()

    if status not in (200, 201):
        error = (
            result.get("error")
            or result.get("detail")
            or result.get("message")
            or str(result)
        )

        await callback.message.answer(
            f"❌ Buyurtma berishda xatolik:\n{error}"
        )

        await state.clear()
        return

    order_id = result.get("id")

    if not order_id:
        await callback.message.answer(
            "❌ Server buyurtma raqamini qaytarmadi."
        )
        await state.clear()
        return

    total_price = result.get("total_price", 0)
    status_value = result.get("status", "pending")

    user_orders.setdefault(user_id, []).append(order_id)

    carts[user_id] = {}

    await callback.message.answer(
        f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
        f"🆔 Buyurtma raqami: #{order_id}\n"
        f"💵 Jami: {float(total_price):,.0f} so'm\n"
        f"📦 Holati: {status_value}\n\n"
        f"Holatni tekshirish:\n"
        f"/order_{order_id}",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )

    await state.clear()


@router.callback_query(F.data == "cancel_order")
async def cancel_checkout(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()

    await callback.answer()

    await callback.message.answer(
        "❌ Buyurtma bekor qilindi.",
        reply_markup=main_menu_kb(),
    )


STATUS_LABELS = {
    "pending": "⏳ Kutilmoqda",
    "preparing": "👨‍🍳 Tayyorlanmoqda",
    "on_the_way": "🛵 Yo'lda",
    "delivered": "✅ Yetkazildi",
    "cancelled": "❌ Bekor qilindi",
}


@router.message(F.text == "📦 Buyurtmalarim")
async def my_orders(message: Message):
    user_id = message.from_user.id
    order_ids = user_orders.get(user_id, [])

    if not order_ids:
        await message.answer(
            "📦 Sizda hali buyurtmalar yo'q."
        )
        return

    for order_id in order_ids[-5:]:
        order = await get_order(order_id)

        if not order:
            continue

        status = order.get("status", "pending")
        status_label = STATUS_LABELS.get(
            status,
            status,
        )

        total_price = order.get("total_price", 0)

        await message.answer(
            f"🆔 Buyurtma #{order['id']}\n"
            f"📦 Holati: {status_label}\n"
            f"💵 Jami: {float(total_price):,.0f} so'm"
        )


@router.message(
    lambda message: (
        message.text
        and message.text.startswith("/order_")
    )
)
async def check_order_status(message: Message):
    try:
        order_id = int(
            message.text.split("_", 1)[1]
        )
    except (IndexError, ValueError):
        await message.answer(
            "❌ Noto'g'ri buyurtma raqami."
        )
        return

    order = await get_order(order_id)

    if not order:
        await message.answer(
            "❌ Bunday buyurtma topilmadi."
        )
        return

    status = order.get("status", "pending")

    status_label = STATUS_LABELS.get(
        status,
        status,
    )

    total_price = order.get("total_price", 0)

    await message.answer(
        f"🆔 Buyurtma #{order['id']}\n"
        f"📦 Holati: {status_label}\n"
        f"💵 Jami: {float(total_price):,.0f} so'm"
    )


async def main():
    bot = Bot(token=BOT_TOKEN)

    dp = Dispatcher(
        storage=MemoryStorage()
    )

    dp.include_router(router)

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())