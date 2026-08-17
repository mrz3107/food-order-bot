import aiohttp
from config import API_URL


async def get_menu():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/menu") as resp:
            if resp.status != 200:
                return []
            return await resp.json()


async def get_menu_item(item_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/menu") as resp:
            print("MENU STATUS:", resp.status)

            if resp.status != 200:
                print("MENU ERROR:", await resp.text())
                return None

            items = await resp.json()

            for item in items:
                if item["id"] == item_id:
                    return item

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

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_URL}/orders",
            json=payload
        ) as resp:
            data = await resp.json()
            return resp.status, data


async def get_order(order_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_URL}/orders/{order_id}"
        ) as resp:
            if resp.status != 200:
                return None

            return await resp.json()