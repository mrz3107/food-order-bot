import aiohttp
from config import API_URL


async def get_menu():
    print("API URL:", API_URL)

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/menu") as resp:
            print("MENU STATUS:", resp.status)

            text = await resp.text()
            print("MENU DATA:", text)

            try:
                return await resp.json()
            except Exception:
                return []


async def get_menu_item(item_id: int):
    print("QIDIRILAYOTGAN ID:", item_id)

    items = await get_menu()

    for item in items:
        print("TEKSHIRILDI:", item["id"])

        if int(item["id"]) == int(item_id):
            print("TOPILDI:", item)
            return item

    print("ITEM TOPILMADI:", item_id)
    return None


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


async def get_order(order_id: int):
    print("ORDER ID:", order_id)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_URL}/orders/{order_id}"
        ) as resp:

            print("GET ORDER STATUS:", resp.status)

            if resp.status != 200:
                print("GET ORDER ERROR:", await resp.text())
                return None

            return await resp.json()