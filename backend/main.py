from fastapi import FastAPI, HTTPException

app = FastAPI(title="Food Order API")


@app.get("/")
def home():
    return {"message": "Food Order API ishlayapti!"}


@app.get("/menu")
def get_menu():
    return [
        {
            "id": 1,
            "name": "Burger",
            "description": "Mol go'shtli mazali burger",
            "price": 25000,
            "available": True
        },
        {
            "id": 2,
            "name": "Pizza",
            "description": "Pishloqli va mazali pizza",
            "price": 45000,
            "available": True
        },
        {
            "id": 3,
            "name": "Lavash",
            "description": "Tovuqli lavash",
            "price": 30000,
            "available": True
        },
        {
            "id": 4,
            "name": "Fri",
            "description": "Qarsildoq kartoshka fri",
            "price": 15000,
            "available": True
        },
        {
            "id": 5,
            "name": "Coca Cola",
            "description": "Sovuq ichimlik",
            "price": 10000,
            "available": True
        }
    ]


@app.get("/menu/{item_id}")
def get_menu_item(item_id: int):
    menu = get_menu()

    for item in menu:
        if item["id"] == item_id:
            return item

    raise HTTPException(
        status_code=404,
        detail="Menu item topilmadi"
    )