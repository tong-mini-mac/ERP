"""Resto menus + ingredients (demo-ready vertical)."""

from __future__ import annotations

from typing import Any

INGREDIENT_NAMES = [
    "Jasmine rice", "Shrimp", "Holy basil", "Garlic", "Thai chili",
    "Chicken breast", "Pork mince", "Coconut milk", "Fish sauce", "Palm sugar",
    "Lime", "Lemongrass", "Galangal", "Kaffir lime leaf", "Egg",
    "Tofu", "Bean sprout", "Rice noodle", "Egg noodle", "Mushroom",
    "Onion", "Tomato", "Cucumber", "Carrot", "Cabbage",
    "Cooking oil", "Soy sauce", "Oyster sauce", "Vinegar", "Salt",
    "Black pepper", "Coriander", "Mint", "Peanut", "Cashew",
    "Squid", "Mussels", "Crab meat", "Beef", "Duck",
    "Potato", "Corn", "Green bean", "Eggplant", "Pumpkin",
    "Milk", "Butter", "Cheese", "Flour", "Sugar",
]

MENU_NAMES = [
    "Pad Kra Pao Chicken", "Tom Yum Goong", "Green Curry", "Pad Thai",
    "Fried Rice Shrimp", "Som Tum", "Mango Sticky Rice", "Massaman Beef",
    "Basil Pork Rice", "Tom Kha Gai", "Cashew Chicken", "Garlic Pepper Pork",
    "Seafood Fried Rice", "Clear Soup", "Spring Rolls", "Chicken Satay",
    "Mango Salad", "Pineapple Fried Rice", "Drunken Noodles", "Boat Noodles",
    "Khao Soi", "Moo Ping", "Grilled Fish", "Crispy Pork Belly",
    "Vegetable Curry", "Eggplant Stir Fry", "Garlic Broccoli", "Corn Soup",
    "Iced Thai Tea", "Iced Coffee", "Coconut Smoothie", "Lemonade",
    "Mango Smoothie", "Chocolate Cake", "Pudding", "Fruit Platter",
    "Club Sandwich", "Chicken Burger", "Veggie Wrap", "French Fries",
    "Onion Rings", "Caesar Salad", "Garden Salad", "Garlic Bread",
    "Pizza Margherita", "Spaghetti Carbonara", "Carbonara Thai Style", "Omelette Rice",
    "Congee", "Waffle Set",
]


def build_resto(skus: list[dict], warehouses: list[dict]) -> dict[str, Any]:
    ingredients: list[dict[str, Any]] = []
    for i in range(50):
        sku = skus[i % len(skus)]
        wh = warehouses[i % len(warehouses)]
        name = INGREDIENT_NAMES[i % len(INGREDIENT_NAMES)]
        if i >= len(INGREDIENT_NAMES):
            name = f"{name} #{i + 1}"
        ingredients.append(
            {
                "id": f"ing-{i + 1:02d}",
                "name": name,
                "unit": ["kg", "g", "ml", "l", "pcs"][i % 5],
                "on_hand": 10 + (i * 3) % 90,
                "yield_pct": 55 + (i % 40),
                "purchase_price": round(5 + (i * 2.35) % 120, 2),
                "erp_sku_id": sku["id"],
                "erp_warehouse_id": wh["id"],
                "notes": "Demo ingredient",
            }
        )

    menus: list[dict[str, Any]] = []
    for i in range(50):
        name = MENU_NAMES[i % len(MENU_NAMES)]
        if i >= len(MENU_NAMES):
            name = f"{name} #{i + 1}"
        ings = [
            {
                "ingredient_id": ingredients[(i + j) % 50]["id"],
                "qty": round(0.05 + (j + 1) * 0.1, 2),
            }
            for j in range(3)
        ]
        menus.append(
            {
                "id": f"menu-{i + 1:02d}",
                "name": name,
                "name_en": name,
                "category": ["main", "soup", "dessert", "drink", "other"][i % 5],
                "selling_price": 59 + (i * 7) % 250,
                "items": [
                    {"id": f"mi-{i + 1}-{k}", "name": name, "price": 59 + (i * 7) % 250}
                    for k in range(1)
                ],
                "recipe": ings,
                "status": "active",
            }
        )

    return {"MENUS": menus, "INGREDIENTS": ingredients}
