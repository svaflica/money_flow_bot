from telebot import types
import os
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
import yaml

from bot import BaseBot

CONFIG_PATH = '/config/config.yaml'

with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

bot = BaseBot(config)
MAX_ERRORS = bot.max_errors


@bot.bot.message_handler(commands=['start'])
def start_message(message):
    bot.bot.send_message(message.chat.id,'Привет')
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    for f in bot.functions:
        markup.add(types.KeyboardButton(f))
    bot.bot.send_message(message.chat.id,'Выбирай, что нужно сделать', reply_markup=markup)

@bot.bot.message_handler(commands=['button'])
def button_message(message):
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    for f in bot.functions:
        markup.add(types.KeyboardButton(f))
    bot.bot.send_message(message.chat.id,'Выбирай, что нужно сделать', reply_markup=markup)


def see_plan(user_id):
    result = bot.db.select_plan_by_chat_id(user_id)
    if result is None or len(result) == 0:
        return 'У вас нет плана на месяц'
    details = "\n".join(["\t- " + value[0] + ": " + (str(value[1]) if value[1] != -1 else 'Не указано') for value in result])
    return f'Детализация:\n{details}'


def add_category(message):
    global MAX_ERRORS
    cache_val = bot.cache.get(str(message.chat.id) + 'add')
    v = message.text
    error = False
    if v.isdigit() and int(v) > 0:
        cache_val['data'].append({'category_id': bot.categories[cache_val['category_id']], 'value': int(v)})
    elif v == 'N':
        cache_val['data'].append({'category_id': bot.categories[cache_val['category_id']], 'value': -1})
    elif MAX_ERRORS <= 0:
        MAX_ERRORS = bot.max_errors
        bot.bot.send_message(message.chat.id, f"Было слишком много ошибок ({bot.max_errors}). Операция прервана.")
        bot.cache.delete(str(message.chat.id) + 'add')
        return
    else:
        MAX_ERRORS -= 1
        bot.bot.send_message(message.chat.id, f"Введите целое число больше 0 или N")
        error = True

    cache_val['category_id'] += error != True
    bot.cache.set(str(message.chat.id) + 'add', cache_val)
    if cache_val['category_id'] == len(bot.categories):
        for idx in range(len(cache_val['data'])):
            cache_val['data'][idx]['chat_id'] = str(message.chat.id)
        bot.db.insert_plan(cache_val['data'])

        MAX_ERRORS = bot.max_errors
        bot.bot.send_message(message.chat.id, f"План успешно добавлен!")
        bot.cache.delete(str(message.chat.id) + 'add')
    else:
        bot.bot.send_message(message.chat.id, f"Введите сумму, которую вы хотите потратить за месяц в категории {bot.categories[cache_val['category_id']]}")
        bot.bot.register_next_step_handler(message, add_category)

def add_plan(message):
    old_result = bot.db.select_plan_by_chat_id(message.chat.id)
    if old_result is not None and len(old_result) > 0:
        bot.bot.send_message(message.chat.id, "У вас уже есть план, его можно только изменить :)")
        return
    bot.bot.send_message(message.chat.id, "Если вам не нужна детализация по какой-то категории, введите N\nНачнём\n")
    bot.cache.set(str(message.chat.id) + 'add', {'data': [], 'category_id': 0})
    bot.bot.send_message(message.chat.id, f"Введите сумму, которую вы хотите потратить за месяц в категории {bot.categories[0]}")
    bot.bot.register_next_step_handler(message, add_category)


def edit_category(message):
    global MAX_ERRORS
    cache_val = bot.cache.get(str(message.chat.id) + 'edit')
    v = message.text
    error = False
    if v.isdigit() and int(v) > 0:
        cache_val['data'][cache_val['category_id']]['value'] = int(v)
    elif v == 'N':
        cache_val['data'][cache_val['category_id']]['value'] = -1
    elif v == 'Y':
        pass
    elif MAX_ERRORS == 0:
        MAX_ERRORS = bot.max_errors
        bot.bot.send_message(message.chat.id, f"Было слишком много ошибок ({bot.max_errors})")
        bot.cache.delete(str(message.chat.id) + 'edit')
        return
    else:
        MAX_ERRORS -= 1
        bot.bot.send_message(message.chat.id, f"Введите целое число больше 0 или N, или Y")
        error = True

    cache_val['category_id'] += error != True
    bot.cache.set(str(message.chat.id) + 'edit', cache_val)
    if cache_val['category_id'] == len(cache_val['data']):
        bot.db.update_plan(cache_val['data'])
        MAX_ERRORS = bot.max_errors
        bot.cache.delete(str(message.chat.id) + 'edit')
        bot.bot.send_message(message.chat.id, f"План успешно обновлен!")
    else:
        bot.bot.send_message(message.chat.id, f"Введите сумму, которую вы хотите потратить за месяц в категории {bot.categories[cache_val['category_id']]}")
        bot.bot.register_next_step_handler(message, edit_category)

def edit_plan(message):
    old_result = bot.db.select_plan_by_chat_id(message.chat.id)
    if old_result is None or len(old_result) == 0:
        bot.bot.send_message(message.chat.id, "У вас нет плана, так что менять тоже нечего :)")
        return

    old_result = [{'category_id': res_item[0], 'value': res_item[1], 'chat_id': res_item[2]} for res_item in old_result]
    bot.bot.send_message(message.chat.id, "Если вам не надо менять какую-то категорию, введите Y, если не нужна детализация по какой-то категории, введите N\nНачнём\n")
    bot.cache.set(str(message.chat.id) + 'edit', {'data': old_result, 'category_id': 0})
    bot.bot.send_message(message.chat.id, f"Введите сумму, которую вы хотите потратить за месяц в категории {old_result[0]['category_id']}")
    bot.bot.register_next_step_handler(message, edit_category)


def add_money_flow(message):
    global MAX_ERRORS
    text = message.text
    val = bot.cache.get(str(message.chat.id) + 'addflow')

    if text in bot.categories:
        val[0]['category_id'] = text

        bot.cache.set(str(message.chat.id) + 'addflow', val)
        bot.bot.send_message(message.chat.id, 'Введите сумму')
        bot.bot.register_next_step_handler(message, add_money_flow)
    elif MAX_ERRORS == 0:
        MAX_ERRORS = bot.max_errors
        bot.bot.send_message(message.chat.id, f"Было слишком много ошибок ({bot.max_errors})")
        bot.cache.delete(str(message.chat.id) + 'addflow')
        return
    elif len(val[0]) == 2:
        bot.bot.send_message(message.chat.id, 'Выберите категорию из предложенного списка в клавиатуре')
        MAX_ERRORS -= 1
        bot.bot.register_next_step_handler(message, add_money_flow)
    else:
        val = bot.cache.get(str(message.chat.id) + 'addflow')
        if len(val[0]) == 3:
            if text.isdigit() and int(text) > 0:
                val[0]['value'] = int(text)
                bot.cache.set(str(message.chat.id) + 'addflow', val)
                bot.bot.send_message(message.chat.id, 'Введите описание траты')
                bot.bot.register_next_step_handler(message, add_money_flow)
            elif MAX_ERRORS == 0:
                MAX_ERRORS = bot.max_errors
                bot.bot.send_message(message.chat.id, f"Было слишком много ошибок ({bot.max_errors})")
                bot.cache.delete(str(message.chat.id) + 'addflow')
                return
            else:
                bot.bot.send_message(message.chat.id, 'Введите сумму больше 0')
                MAX_ERRORS -= 1
                bot.bot.register_next_step_handler(message, add_money_flow)
        else:
            val[0]['description'] = text
            val[0]['chat_id'] = message.chat.id
            bot.db.insert_flow(val)
            markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
            for f in bot.functions:
                markup.add(types.KeyboardButton(f))
            bot.bot.send_message(message.chat.id, f'Трата успешно добавлена {val}', reply_markup=markup)


@bot.bot.callback_query_handler(func=lambda call: call.data in ["add", "edit", "flow_in", "flow_out"])
def callback_worker(call):
    if call.data == "add":
        add_plan(call.message)
    elif call.data == "edit":
        edit_plan(call.message)
    elif call.data == "flow_in" or call.data == "flow_out":
        bot.cache.set(str(call.message.chat.id) + 'addflow', [{'flow_type_id': call.data.split('_')[-1]}])
        calendar, step = DetailedTelegramCalendar().build()
        bot.bot.send_message(call.message.chat.id,
                        f"Select {LSTEP[step]}",
                        reply_markup=calendar)

@bot.bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal(call):
    result, key, step = DetailedTelegramCalendar().process(call.data)
    if not result and key:
        bot.bot.edit_message_text(f"Select {LSTEP[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        bot.bot.edit_message_text(f"You selected {result}",
                              call.message.chat.id,
                              call.message.message_id)
        cache_value = bot.cache.get(str(call.message.chat.id) + 'addflow')
        cache_value[0]['date'] = str(result)

        bot.cache.set(str(call.message.chat.id) + 'addflow', cache_value)
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        for f in bot.categories:
            markup.add(types.KeyboardButton(f))
        bot.bot.send_message(call.message.chat.id, 'Выберите категорию расходов', reply_markup=markup)
        bot.bot.register_next_step_handler(call.message, add_money_flow)


@bot.bot.message_handler(content_types='text')
def message_reply(message):
    if message.text == "Посмотреть план на месяц":
        bot.bot.send_message(message.chat.id, see_plan(message.chat.id))
    elif message.text == "Добавить/Изменить план на месяц":
        keyboard = types.InlineKeyboardMarkup()
        key_add = types.InlineKeyboardButton(text='Добавить', callback_data='add')
        keyboard.add(key_add)
        key_edit= types.InlineKeyboardButton(text='Изменить', callback_data='edit')
        keyboard.add(key_edit)
        bot.bot.send_message(message.chat.id, text="Хорошо, выберите, что хотите сделать", reply_markup=keyboard)
    elif message.text == "Добавить трату/поступление":
        keyboard = types.InlineKeyboardMarkup()
        key_add = types.InlineKeyboardButton(text='Трата', callback_data='flow_out')
        keyboard.add(key_add)
        key_edit= types.InlineKeyboardButton(text='Поступление', callback_data='flow_in')
        keyboard.add(key_edit)
        bot.bot.send_message(message.chat.id, text="Хорошо, выберите, что хотите сделать", reply_markup=keyboard)
    elif message.text == "Очистить данные":
        # file_name = os.path.join('files', str(message.chat.id) + '.json')
        # os.remove(file_name)
        bot.bot.send_message(message.chat.id, text="Все данные о вас успешно очищены")

bot.bot.polling(none_stop=True)
