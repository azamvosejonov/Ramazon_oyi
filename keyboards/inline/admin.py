
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

menu_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Samarqand",callback_data='Samarqand'),
            InlineKeyboardButton(text="Qarshi",callback_data='Qarshi'),
        ],
        [
            InlineKeyboardButton(text="Andijon",callback_data="Andijon"),
            InlineKeyboardButton(text="Far`gona",callback_data="Fargona"),
        ],
        [
            InlineKeyboardButton(text="Namangan",callback_data="Namangan"),
            InlineKeyboardButton(text="Toshkent",callback_data="Toshkent"),
        ],
        [
            InlineKeyboardButton(text="Xiva", callback_data='Xiva'),
            InlineKeyboardButton(text="Navoiy", callback_data='Navoiy'),
        ],
        [
            InlineKeyboardButton(text="Buxoro", callback_data="Buxoro"),
            InlineKeyboardButton(text="Guliston", callback_data="Guliston"),
        ],
        [
            InlineKeyboardButton(text="Qo`qon", callback_data="Qo`qon"),
            InlineKeyboardButton(text="Jizzax", callback_data="Jizzax"),
        ],
        [
            InlineKeyboardButton(text="Keyingisi➡️", callback_data="keng"),
        ],
    ]
)


menu_orqa = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="To`xtatish", callback_data="or"),
        ],
    ])

menu_boshqa = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Marg`ilon", callback_data="Margilon"),
            InlineKeyboardButton(text="Nurota", callback_data="Nurata"),
        ],
        [
            InlineKeyboardButton(text="Angren", callback_data="Angren"),
            InlineKeyboardButton(text="Xonobot", callback_data="Xonobot"),
        ],
        [
            InlineKeyboardButton(text="Jomboy", callback_data="Jomboy"),
            InlineKeyboardButton(text="Mo`ynok", callback_data="Moynok"),
        ],
        [
            InlineKeyboardButton(text="Katta qo`rg`on", callback_data="Kattaqorgon"),
            InlineKeyboardButton(text="Denov", callback_data="Denov"),
        ],
        [
            InlineKeyboardButton(text="Orqa⬅️", callback_data="or"),
        ],
    ])




