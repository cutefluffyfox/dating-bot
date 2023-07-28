from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.input_media import InputMediaPhoto

from modules.models import User


def generate_inline_markup(*args) -> InlineKeyboardMarkup:
    """
    Generate inline markup by list of dicts with parameters
    """
    keyboard = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for element in args:
        if type(element) == dict and element:
            keyboard.add(InlineKeyboardButton(**element))
        else:
            keyboard.add(*[InlineKeyboardButton(**button) for button in element])
    return keyboard


class InlineButtons:
    @staticmethod
    def edit_profile():
        return generate_inline_markup(
            {'text': 'Изменить фото', 'callback_data': 'edit/image'},
            {'text': 'Изменить имя', 'callback_data': 'edit/name'},
            {'text': 'Изменить местоимения', 'callback_data': 'edit/pronouns'},
            {'text': 'Изменить описание', 'callback_data': 'edit/info'},
            {'text': '« К карусели', 'callback_data': 'find/'}
        )


class Pages:
    default_profile_image = 'AgACAgIAAxkBAAIeCGTD4fKDSi4S6-7Iz8g3_4Jg4SwlAAJKyzEbUTcgSlIiOnPYXL7LAQADAgADcwADLwQ'
    default_profile_name = '<ваше имя/никнейм>'
    default_profile_pronouns = '<ваши местоимения>'
    default_profile_description = '<тут ваше прекрасное био>'

    @staticmethod
    def my_profile(user: User, message_id: int = None) -> dict:
        caption = '%name% | %pronouns%\n\n%description%'
        caption = caption.replace('%name%', Pages.default_profile_name if (user.name is None) else user.name)
        caption = caption.replace('%pronouns%', Pages.default_profile_pronouns if (user.pronouns is None) else user.pronouns)
        caption = caption.replace('%description%', Pages.default_profile_description if (user.description is None) else user.description)

        photo = Pages.default_profile_image if (user.file_id is None) else user.file_id

        page = {
            'chat_id': user.user_id,
            'reply_markup': InlineButtons.edit_profile()
        }

        if message_id is None:
            page = {**page, 'photo': photo, 'caption': caption}
        else:
            page = {**page, 'message_id': message_id, 'media': InputMediaPhoto(media=photo, caption=caption)}

        return page

