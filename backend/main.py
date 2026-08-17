@router.message(F.text == "🛒 Savat")
async def show_cart(message: Message):
    user_id = message.from_user.id
    cart = carts.get(user_id, {})

    if not cart:
        await message.answer(
            "Savatingiz bo'sh. Avval menyudan taom tanlang 🍽"
        )
        return

    # API dan butun menyuni olamiz
    items = await get_menu()

    if not items:
        await message.answer("❌ Menyuni olishda xatolik.")
        return

    # ID bo'yicha mahsulotlarni topish uchun
    menu_dict = {
        int(item["id"]): item
        for item in items
    }

    lines = []
    total = 0

    for item_id, qty in cart.items():
        item = menu_dict.get(int(item_id))

        if not item:
            continue

        subtotal = item["price"] * qty
        total += subtotal

        lines.append(
            f"🍽 {item['name']} x{qty} = {subtotal:,.0f} so'm"
        )

    if not lines:
        await message.answer(
            "❌ Savatdagi mahsulotlarni topib bo'lmadi."
        )
        return

    text = (
        "🛒 Sizning savatingiz:\n\n"
        + "\n".join(lines)
        + f"\n\n💵 Jami: {total:,.0f} so'm"
    )

    await message.answer(
        text,
        reply_markup=cart_kb()
    )