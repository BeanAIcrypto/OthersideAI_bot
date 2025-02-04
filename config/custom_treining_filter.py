from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types
from db.dbworker import create_user, load_user_data, save_user_data


class UserDataMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        user_id = message.from_user.id
        user_id_str = str(user_id)

        user_data = load_user_data()
        print(user_data)

        user_info = user_data.get(user_id_str)

        if user_info:
            message.user_language = user_data[user_id_str]['language']
        else:
            create_user(user_id_str, message.from_user.username)
            user_data[user_id_str] = {'language': 'None'}
            save_user_data(user_data)

            message.user_language = 'None'

            user_data = load_user_data()
            message.user_language = user_data[user_id_str]['language']


    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        user_id = callback_query.from_user.id
        user_id_str = str(user_id)
        user_data = load_user_data()
        print(user_data)
        user_info = user_data.get(user_id_str)

        if user_info:
            callback_query.user_language = user_data[user_id_str]['language']
        else:
            create_user(user_id_str, callback_query.from_user.username)
            user_data[user_id_str] = {'language': 'None'}
            save_user_data(user_data)

            callback_query.user_language = 'None'

            user_data = load_user_data()
            callback_query.user_language = user_data[user_id_str]['language']


def setup_middlewares(dp):
    dp.middleware.setup(UserDataMiddleware())
