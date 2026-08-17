@router.message(F.text == "🛒 Savat")
async def show_cart(message: Message):
    user_id = message.from_user.id
    cart = carts.get(user_id, {})

    if not cart:
        await message.answer(
            "Savatingiz bo'sh. Avval menyudan taom tanlang 🍽"
        )
        return

    lines = []
    total = 0

    for item_id, qty in cart.items():
        item = await get_menu_item(item_id)

        if not item:
            await message.answer(
                f"❌ {item_id}-raqamli mahsulotni backenddan topib bo'lmadi."
            )
            continue

        subtotal = item["price"] * qty
        total += subtotal

        lines.append(
            f"🍽 {item['name']} x{qty} = {subtotal:,.0f} so'm"
        )

    if not lines:
        await message.answer(
            "Savatdagi mahsulotlarni olishda xatolik yuz berdi."
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
        parse_mode="HTML"
    )