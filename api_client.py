async def create_order(
    customer_name: str,
    customer_phone: str,
    address: str,
    items: list
):
    payload = {
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "address": address,
        "items": items,
    }

    print("ORDER URL:", f"{API_URL}/orders")
    print("ORDER PAYLOAD:", payload)

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_URL}/orders",
            json=payload
        ) as resp:

            print("ORDER STATUS:", resp.status)

            text = await resp.text()

            print("ORDER RESPONSE:", text)

            try:
                data = await resp.json()
            except Exception:
                data = {"error": text}

            return resp.status, data