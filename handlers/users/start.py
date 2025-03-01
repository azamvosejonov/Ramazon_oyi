import asyncio
from datetime import datetime, time, timedelta
from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from keyboards.inline.admin import menu_inline, menu_orqa,menu_boshqa
from keyboards.default.duo import menu_buttons
from aiogram.types import CallbackQuery
from loader import dp, bot

# Toshkent uchun Ramazon taqvimi (saharlik va iftorlik vaqtlarini rasmga qarab yozildi)
toshkent_vaqtlar = [
    (time(5, 40), time(18, 17)), (time(5, 38), time(18, 18)),
    (time(5, 37), time(18, 19)), (time(5, 35), time(18, 20)),
    (time(5, 33), time(18, 21)), (time(5, 32), time(18, 22)),
    (time(5, 30), time(18, 24)), (time(5, 29), time(18, 25)),
    (time(5, 27), time(18, 26)), (time(5, 25), time(18, 27)),
    (time(5, 24), time(18, 28)), (time(5, 22), time(18, 29)),
    (time(5, 20), time(18, 30)), (time(5, 18), time(18, 32)),
    (time(5, 17), time(18, 33)), (time(5, 15), time(18, 34)),
    (time(5, 13), time(18, 35)), (time(5, 12), time(18, 36)),
    (time(5, 10), time(18, 37)), (time(5, 8), time(18, 38)),
    (time(5, 6), time(18, 39)), (time(5, 4), time(18, 40)),
    (time(5, 3), time(18, 41)), (time(5, 1), time(18, 42)),
    (time(4, 59), time(18, 44)), (time(4, 57), time(18, 45)),
    (time(4, 55), time(18, 46)), (time(4, 54), time(18, 47)),
    (time(4, 52), time(18, 48)), (time(4, 50), time(18, 49)),
]

# Shaharlar uchun vaqt farqlari
shahar_vaqt_farqlari = {
    "Samarqand": timedelta(minutes=9),
    "Andijon": timedelta(minutes=-12),
    "Qo'qon": timedelta(minutes=-7),
    "Namangan": timedelta(minutes=-10),
    "Fargona": timedelta(minutes=-10),
    "Margilon": timedelta(minutes=-10),
    "Toshkent": timedelta(minutes=0),
    "Jizzax": timedelta(minutes=6),
    "Qarshi": timedelta(minutes=14),
    "Navoiy": timedelta(minutes=16),
    "Nurata": timedelta(minutes=14),
    "Angren": timedelta(minutes=-3),
    "Xonobot": timedelta(minutes=-13),
    "Jomboy": timedelta(minutes=7),
    "Guliston": timedelta(minutes=2),
    "Xiva": timedelta(minutes=36),
    "Moynok": timedelta(minutes=41),
    "Kattaqorgon": timedelta(minutes=12),
    "Denov": timedelta(minutes=6),
}


async def send_notification():
    while True:
        now = datetime.now().time()
        sana_index = datetime.now().day - 1  # Hozirgi kun bo'yicha indeks
        if sana_index >= len(toshkent_vaqtlar):
            sana_index = len(toshkent_vaqtlar) - 1

        t_saharlik, t_iftorlik = toshkent_vaqtlar[sana_index]

        for shahar, vaqt_farhi in shahar_vaqt_farqlari.items():
            adjusted_saharlik = (
                        datetime.combine(datetime.today(), t_saharlik) + vaqt_farhi - timedelta(minutes=2)).time()
            adjusted_iftorlik = (
                        datetime.combine(datetime.today(), t_iftorlik) + vaqt_farhi + timedelta(minutes=1)).time()
            o_url = 'https://imgur.com/a/4Mmbdk8'
            y_url = 'https://imgur.com/a/GW0se1q'

            if now.hour == adjusted_saharlik.hour and now.minute == adjusted_saharlik.minute:
                await bot.send_message(123456789,
                                       f"{shahar} uchun saharlik vaqti yaqinlashmoqda! {adjusted_saharlik.strftime('%H:%M')}",y_url)

            if now.hour == adjusted_iftorlik.hour and now.minute == adjusted_iftorlik.minute:
                await bot.send_message(123456789,
                                       f"{shahar} uchun iftorlik vaqti yaqinlashmoqda! {adjusted_iftorlik.strftime('%H:%M')}",o_url)

        await asyncio.sleep(60)  # Har bir daqiqada tekshirish


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    text = ("Assalomu aleykum! Bizning botimiz Ramazon oyida "
            "saharlik va iftorlik vaqtlari haqida ogohlantiradi. "
            "Sizga saharlik va iftorlik duolarini ham yuboramiz!")
    matn = "Qaysi viloyat?"
    await message.answer(matn, reply_markup=menu_buttons)
    await message.answer(text, reply_markup=menu_inline)


@dp.callback_query_handler(lambda call: call.data in shahar_vaqt_farqlari.keys())
async def select_city(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer(
        f"Siz {call.data} shahrini tanladingiz. Endi saharlik va iftorlik vaqtidan oldin sizga xabar yuboriladi!",
        reply_markup=menu_orqa)




@dp.callback_query_handler(text="or")
async def course_callback_message(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer("Orqa",reply_markup=menu_inline)

@dp.callback_query_handler(text="keng")
async def course_callback_message(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer("keyin",reply_markup=menu_boshqa)

# Start background task
async def on_startup(dp):
    asyncio.create_task(send_notification())


