from os import getenv
import logging

import dotenv
from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.types.input_media import InputMediaPhoto
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import MessageNotModified
from aiogram.dispatcher import FSMContext
from requests.exceptions import ContentDecodingError, ConnectionError, RetryError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from modules import database
from modules.models import User
from modules.generators import Pages


# Configure logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Initialize environment variables from .env file (if it exists)
dotenv.load_dotenv(dotenv.find_dotenv())
BOT_TOKEN = getenv('BOT_TOKEN')
ADMIN_ID = getenv('ADMIN_ID')
CONNECTION_STRING = getenv('CONNECTION_STRING')


# Check that critical variables are defined
if BOT_TOKEN is None:
    logging.critical('No BOT_TOKEN variable found in project environment')
if CONNECTION_STRING is None:
    logging.critical('No CONNECTION_STRING variable found in project environment')
if ADMIN_ID is None:
    logging.critical('No ADMIN_ID variable found in project environment')
else:
    ADMIN_ID = int(ADMIN_ID)


# Initialize database
database.global_init(CONNECTION_STRING)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# States
class Edit(StatesGroup):
    text = State()
    photo = State()


class Registration(StatesGroup):
    name = State()
    pronouns = State()
    description = State()
    photo = State()


@dp.message_handler(commands=['link'])
async def link(message: Message):
    if message.from_user.username is not None:
        await message.reply('Hello @' + message.from_user.username)
    await message.reply(f'[{message.from_user.first_name}](tg://user?id={message.from_user.id})', parse_mode='MarkdownV2')
    await message.forward(chat_id=message.from_user.id)


@dp.message_handler(commands=['start'])
async def start(message: Message):
    if not User.exists(message.from_user.id):
        User.add(user_id=message.from_user.id)
    user: User = User.get(message.from_user.id)

    await bot.send_message(
        chat_id=message.from_user.id,
        text='Привет, я Фырка - бот для знакомств в чате Flood e2! '
             'Чтобы продолжить давайте познакомимся: ниже я отправила вашу анкету, которую вам надо будет заполнить.'
             'Не стесняйтесь рассказать о себе, чем лучше вы распишите что вас интересует, тем больше людей будут '
             'рады пообщаться с вами! Давайте приступим:'
    )

    new_message = await bot.send_photo(**Pages.my_profile(user))
    user.set(message_id=new_message.message_id)


@dp.callback_query_handler(lambda c: c.data == 'edit/image')
async def my_image(callback_query: CallbackQuery):
    await bot.edit_message_caption(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        caption='Чтобы изменить изображение отправьте пожалуйста фото (не документ/стикер/текст) '
                'которое вы хотите ассоциировать с вами. Это можете быть вы, ваш персонаж, или ваше тотемное животное! '
                'Когда будете готовы можете отправлять!'
    )

    await Edit.photo.set()


@dp.message_handler(content_types=ContentType.ANY, state=Edit.photo)
async def my_image_v2(message: Message, state: FSMContext):
    user: User = User.get(message.from_user.id)

    if message.content_type != ContentType.PHOTO:
        await bot.edit_message_caption(
            chat_id=message.from_user.id,
            message_id=user.message_id,
            caption='Чтобы изменить изображение отправьте пожалуйста фото (не документ/стикер/текст) '
                    'которое вы хотите ассоциировать с вами. Это можете быть вы, ваш персонаж, или ваше тотемное '
                    'животное! Когда будете готовы можете отправлять!\n\nОтправьте пожалуйста **изображение**, '
                    'не документ/стрикер/текст'
        )
        return
    user: User = User.get(message.from_user.id)
    file_id = message.photo[0].file_id
    user.set(file_id=file_id)

    await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
    await bot.edit_message_media(**Pages.my_profile(user, message_id=user.message_id))
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('edit/') and c.data != 'edit/image')
async def my_text(callback_query: CallbackQuery):
    user: User = User.get(callback_query.from_user.id)
    data = callback_query.data.split('/')[1]
    user.set(bot_metadata=data)

    await bot.edit_message_caption(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        caption='Чтобы изменить данные отправьте пожалуйста сообщение (не документ/стикер/фото) '
                'которое вы хотите ассоциировать с вами'
    )
    await Edit.text.set()


@dp.message_handler(content_types=ContentType.ANY, state=Edit.text)
async def my_text_v2(message: Message, state: FSMContext):
    user: User = User.get(message.from_user.id)

    if message.content_type != ContentType.TEXT:
        await bot.edit_message_caption(
            chat_id=message.from_user.id,
            message_id=user.message_id,
            caption='Чтобы изменить данные отправьте пожалуйста сообщение (не документ/стикер/фото) '
                    'которое вы хотите ассоциировать с вами\n\nОтправьте пожалуйста **сообщение**, '
                    'не документ/стрикер/фото'
        )
        return
    user: User = User.get(message.from_user.id)
    data = message.text

    if user.bot_metadata == 'name':
        user.set(name=data)
    elif user.bot_metadata == 'info':
        user.set(description=data)
    elif user.bot_metadata == 'pronouns':
        user.set(pronouns=data)

    await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
    await bot.edit_message_media(**Pages.my_profile(user, message_id=user.message_id))
    await state.finish()


@dp.message_handler(commands=['start', 'login', 'register'])
async def start(message: Message):
    await bot.send_message(
        chat_id=message.from_user.id,
        text='Привет, это бот для знакомств в чате Flood e2! Чтобы продолжить давайте познакомимся, как к вас зовут? (имя + фамилия / никнейм)'
    )
    await Registration.first()


@dp.message_handler(state=Registration.name)
async def register_name(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await Registration.next()

    await bot.send_message(
        chat_id=message.from_user.id,
        text='Какие местоимения вы исспользуете?'
    )


@dp.message_handler(state=Registration.pronouns)
async def register_pronouns(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['pronouns'] = message.text
    await Registration.next()

    await bot.send_message(
        chat_id=message.from_user.id,
        text='Расскажите о себе: откуда вы, какие у вас хобби, чем занимаетесь в жизни, что вас мотивирует, какие планы на жизнь, что хотите от знакомства'
    )


@dp.message_handler(state=Registration.description)
async def register_description(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text
    await Registration.next()

    await bot.send_message(
        chat_id=message.from_user.id,
        text='И для завершения отправьте аватарку которую вы хотите исспользовать с вами'
    )


@dp.message_handler(content_types=ContentType.PHOTO, state=Registration.photo)
async def register_photo(message: Message, state: FSMContext):
    data = await state.get_data()  # message.photo[0].file_id

    # bad code style, need fix
    user: User = User.get(message.from_user.id)
    if user is not None:
        user.delete()

    User.add(
        user_id=message.from_user.id,
        name=data['name'],
        pronouns=data['pronouns'],
        description=data['description'],
        file_id=message.photo[0].file_id
    )

    user: User = User.get(message.from_user.id)

    await bot.send_photo(
        chat_id=message.from_user.id,
        photo=user.file_id,
        caption=f'{user.name} | {user.pronouns}\n'
                f'\n'
                f'{user.description}'
    )

    await state.finish()


@dp.message_handler(content_types=ContentType.ANY, state=Registration.photo)
async def register_not_photo(message: Message, state: FSMContext):
    await bot.send_message(
        chat_id=message.from_user.id,
        text='Отправьте пожалуйста изображение, не документ/стикер/текст'
    )


@dp.message_handler()
async def any_message(message: Message):
    await bot.send_message(
        chat_id=message.from_user.id,
        text='L'
    )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
