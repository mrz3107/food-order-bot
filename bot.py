@router.message(F.text == "🛒 Savat")
async def show_cart(message: Message):
    user_id = message.from_user.id
    cart = carts.get(user_id, {})

    print("CART DEBUG:", cart)

    if not cart:
        await message.answer(
            "Savatingiz bo'sh. Avval menyudan taom tanlang 🍽"
        )
        return

    items = await get_menu()

    print("MENU DEBUG:", items)

    lines = []
    total = 0

    for item_id, qty in cart.items():
        for item in items:
            if int(item["id"]) == int(item_id):
                subtotal = item["price"] * qty
                total += subtotal

                lines.append(
                    f"🍽 {item['name']} x{qty} = {subtotal:,.0f} so'm"
                )
                break

    if not lines:
        await message.answer(
            f"❌ Mahsulot topilmadi.\n\n"
            f"Cart: {cart}\n"
            f"API menu: {items}"
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