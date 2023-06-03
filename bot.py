import telebot
from telebot import types
import os
import json
import redis
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

redis_client = redis.Redis(host='localhost', port=6379, db=0)

EXPIRE_TIME = 60 * 60 * 48
MAX_ERRORS_DEFAULT = 5
MAX_ERRORS = MAX_ERRORS_DEFAULT
FUNTIONS = [
      "Посмотреть план на месяц",
      "Добавить/Изменить план на месяц",
      "Статистика за период",
      "Добавить трату",
      "Очистить данные"
]

with open('src/categories.json', 'r') as f:
    CATEGORIES = json.load(f)

bot = telebot.TeleBot('')


def serialize(obj):
    return json.dumps(obj, ensure_ascii=False)

def deserialize(obj):
    return json.loads(obj)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id,'Привет')
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    for f in FUNTIONS:
        markup.add(types.KeyboardButton(f))
    bot.send_message(message.chat.id,'Выбирай, что нужно сделать', reply_markup=markup)

@bot.message_handler(commands=['button'])
def button_message(message):
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    for f in FUNTIONS:
        markup.add(types.KeyboardButton(f))
    bot.send_message(message.chat.id,'Выбирай, что нужно сделать', reply_markup=markup)

def see_plan(user_id):
    file_name = os.path.join('files', str(user_id) + '.json')
    if not os.path.exists(file_name):
         return 'У вас нет плана на месяц'
    with open(file_name, 'r') as f:
        data = json.load(f).get('plan', None)

    if data is None:
        return 'У вас нет плана на месяц'
    details = "\n".join(["\t- " + key + ": " + (str(value) if value != -1 else 'Не указано') for key, value in data["categories"].items()])
    return f'Ваш план на месяц:\n\nМаксимальная предполагаемо потраченная сумма: {data["all"]}\n\n'\
           f'Детализация:\n{details}'


def add_result(message):
    global MAX_ERRORS, MAX_ERRORS_DEFAULT
    cache_val = deserialize(redis_client.get(str(message.chat.id) + 'add'))
    v = message.text
    if v.isdigit() and int(v) > 0:
        cache_val['data']['plan']['all'] = int(v)
    elif v == 'N':
        cache_val['data']['plan']['all'] = -1
    elif MAX_ERRORS == 0:
        MAX_ERRORS = MAX_ERRORS_DEFAULT
        bot.send_message(message.chat.id, f"Было слишком много ошибок ({MAX_ERRORS_DEFAULT})")
        return
    else:
        MAX_ERRORS -= 1
        bot.send_message(message.chat.id, f"Введите целое число больше 0 или N")
        bot.register_next_step_handler(message, add_result)

    target_path = os.path.join('files', str(message.chat.id) + '.json')
    if os.path.exists(target_path):
        with open(target_path, 'r') as f:
            last_data = json.load(f)
    else:
        last_data = {}
    last_data['plan'] = cache_val['data']['plan']
    with open(target_path, 'w') as f:
        json.dump(last_data, f, ensure_ascii=False, indent=4)

    bot.send_message(message.chat.id, f"План успешно добавлен!")
    redis_client.delete(str(message.chat.id) + 'add')


def add_category(message):
    global MAX_ERRORS, MAX_ERRORS_DEFAULT
    cache_val = deserialize(redis_client.get(str(message.chat.id) + 'add'))
    v = message.text
    error = False
    if v.isdigit() and int(v) > 0:
        cache_val['data']['plan']['categories'][CATEGORIES[cache_val['category_id']]] = int(v)
    elif v == 'N':
        cache_val['data']['plan']['categories'][CATEGORIES[cache_val['category_id']]] = -1
    elif MAX_ERRORS == 0:
        MAX_ERRORS = MAX_ERRORS_DEFAULT
        bot.send_message(message.chat.id, f"Было слишком много ошибок ({MAX_ERRORS_DEFAULT})")
        return
    else:
        MAX_ERRORS -= 1
        bot.send_message(message.chat.id, f"Введите целое число больше 0 или N")
        error = True

    cache_val['category_id'] += error != True
    redis_client.set(str(message.chat.id) + 'add', serialize(cache_val))
    if cache_val['category_id'] == len(CATEGORIES):
        min_val = sum([val for val in cache_val['data']['plan']['categories'].values() if val != -1])
        bot.send_message(message.chat.id, f"Введите сумму, которую вы хотите потратить за месяц суммарно? (суммарно по категориям сейчас {min_val})")
        bot.register_next_step_handler(message, add_result)
    else:
        bot.send_message(message.chat.id, f"Введите сумму, которую вы хотите потратить за месяц в категории {CATEGORIES[cache_val['category_id']]}")
        bot.register_next_step_handler(message, add_category)

def add_plan(message):
    data = {'plan': {'all': -1, 'categories': {cat: -1 for cat in CATEGORIES}}}
    bot.send_message(message.chat.id, "Если вам не нужна детализация по какой-то категории, введите N\nНачнём\n")
    redis_client.set(str(message.chat.id) + 'add', serialize({'data': data, 'category_id': 0}), EXPIRE_TIME)
    bot.send_message(message.chat.id, f"Введите сумму, которую вы хотите потратить за месяц в категории {CATEGORIES[0]}")
    bot.register_next_step_handler(message, add_category)

def edit_result(message):
    global MAX_ERRORS, MAX_ERRORS_DEFAULT
    cache_val = deserialize(redis_client.get(str(message.chat.id) + 'edit'))
    v = message.text
    if v.isdigit() and int(v) > 0:
        cache_val['data']['plan']['all'] = int(v)
    elif v == 'N':
        cache_val['data']['plan']['all'] = -1
    elif v == 'Y':
        pass
    elif MAX_ERRORS == 0:
        MAX_ERRORS = MAX_ERRORS_DEFAULT
        bot.send_message(message.chat.id, f"Было слишком много ошибок ({MAX_ERRORS_DEFAULT})")
        return
    else:
        MAX_ERRORS -= 1
        bot.send_message(message.chat.id, f"Введите целое число больше 0 или N, или Y")
        bot.register_next_step_handler(message, edit_result)

    target_path = os.path.join('files', str(message.chat.id) + '.json')
    if os.path.exists(target_path):
        with open(target_path, 'r') as f:
            last_data = json.load(f)
    else:
        last_data = {}
    last_data['plan'] = cache_val['data']['plan']
    with open(target_path, 'w') as f:
        json.dump(last_data, f, ensure_ascii=False, indent=4)

    bot.send_message(message.chat.id, f"План успешно обновлен!")
    redis_client.delete(str(message.chat.id) + 'edit')

def edit_category(message):
    global MAX_ERRORS, MAX_ERRORS_DEFAULT
    cache_val = deserialize(redis_client.get(str(message.chat.id) + 'edit'))
    v = message.text
    error = False
    if v.isdigit() and int(v) > 0:
        cache_val['data']['plan']['categories'][CATEGORIES[cache_val['category_id']]] = int(v)
    elif v == 'N':
        cache_val['data']['plan']['categories'][CATEGORIES[cache_val['category_id']]] = -1
    elif v == 'Y':
        pass
    elif MAX_ERRORS == 0:
        MAX_ERRORS = MAX_ERRORS_DEFAULT
        bot.send_message(message.chat.id, f"Было слишком много ошибок ({MAX_ERRORS_DEFAULT})")
        return
    else:
        MAX_ERRORS -= 1
        bot.send_message(message.chat.id, f"Введите целое число больше 0 или N, или Y")
        error = True

    cache_val['category_id'] += error != True
    redis_client.set(str(message.chat.id) + 'edit', serialize(cache_val))
    if cache_val['category_id'] == len(CATEGORIES):
        min_val = sum([val for val in cache_val['data']['plan']['categories'].values() if val != -1])
        bot.send_message(message.chat.id, f"Введите сумму, которую вы хотите потратить за месяц суммарно? (суммарно по категориям сейчас {min_val})")
        bot.register_next_step_handler(message, edit_result)
    else:
        bot.send_message(message.chat.id, f"Введите сумму, которую вы хотите потратить за месяц в категории {CATEGORIES[cache_val['category_id']]}")
        bot.register_next_step_handler(message, edit_category)

def edit_plan(message):
    file_name = os.path.join('files', str(message.chat.id) + '.json')
    if not os.path.exists(file_name):
        bot.send_message(message.chat.id, "У вас нет плана, так что менять тоже нечего :)")
        return

    with open(file_name, 'r') as f:
        data = json.load(f)
    bot.send_message(message.chat.id, "Если вам не надо менять какую-то категорию, введите Y, если не нужна детализация по какой-то категории, введите N\nНачнём\n")
    redis_client.set(str(message.chat.id) + 'edit', serialize({'data': data, 'category_id': 0}), EXPIRE_TIME)
    bot.send_message(message.chat.id, f"Введите сумму, которую вы хотите потратить за месяц в категории {CATEGORIES[0]}")
    bot.register_next_step_handler(message, edit_category)

def add_money_flow(message):
    text = message.text

    if text in CATEGORIES:
        val = deserialize(redis_client.get(str(message.chat.id) + 'addflow'))
        val['category'] = text

        redis_client.set(str(message.chat.id) + 'addflow', serialize(val))
        bot.send_message(message.chat.id, 'Введите сумму')
        bot.register_next_step_handler(message, add_money_flow)
    else:
        val = deserialize(redis_client.get(str(message.chat.id) + 'addflow'))
        if len(val) == 2:
            if text.isdigit() and int(text) > 0:
                val['value'] = int(text)
                redis_client.set(str(message.chat.id) + 'addflow', serialize(val))
                bot.send_message(message.chat.id, 'Введите описание траты')
                bot.register_next_step_handler(message, add_money_flow)
            else:
                bot.send_message(message.chat.id, 'Введите сумму больше 0')
                bot.register_next_step_handler(message, add_money_flow)
        else:
            val['descr'] = text
            file_name = os.path.join('files', str(message.chat.id) + '.json')
            if not os.path.exists(file_name):
                data = {}
            else:
                with open(file_name) as f:
                    data = json.load(f)
            if 'flows' in data:
                data['flows'].append(val)
            else:
                data['flows'] = [val]
            with open(file_name, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
            for f in FUNTIONS:
                markup.add(types.KeyboardButton(f))
            bot.send_message(message.chat.id, f'Трата успешно добавлена {val}', reply_markup=markup)



@bot.callback_query_handler(func=lambda call: call.data in ["add", "edit"])
def callback_worker(call):
    if call.data == "add":
        add_plan(call.message)
    elif call.data == "edit":
        edit_plan(call.message)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal(call):
    result, key, step = DetailedTelegramCalendar().process(call.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"You selected {result}",
                              call.message.chat.id,
                              call.message.message_id)
        if redis_client.exists(str(call.message.chat.id) + 'addflow'):
            redis_client.set(str(call.message.chat.id) + 'addflow', serialize({'date': str(result)}))
            markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
            for f in CATEGORIES:
                markup.add(types.KeyboardButton(f))
            bot.send_message(call.message.chat.id, 'Выберите категорию расходов', reply_markup=markup)
            bot.register_next_step_handler(call.message, add_money_flow)


@bot.message_handler(content_types='text')
def message_reply(message):
    if message.text == "Посмотреть план на месяц":
        bot.send_message(message.chat.id, see_plan(message.chat.id))
    elif message.text == "Добавить/Изменить план на месяц":
        keyboard = types.InlineKeyboardMarkup()
        key_add = types.InlineKeyboardButton(text='Добавить', callback_data='add')
        keyboard.add(key_add)
        key_edit= types.InlineKeyboardButton(text='Изменить', callback_data='edit')
        keyboard.add(key_edit)
        bot.send_message(message.chat.id, text="Хорошо, выберите, что хотите сделать", reply_markup=keyboard)
    elif message.text == "Добавить трату":
        redis_client.set(str(message.chat.id) + 'addflow', serialize({}))
        calendar, step = DetailedTelegramCalendar().build()
        bot.send_message(message.chat.id,
                        f"Select {LSTEP[step]}",
                        reply_markup=calendar)
    elif message.text == "Очистить данные":
        file_name = os.path.join('files', str(message.chat.id) + '.json')
        os.remove(file_name)
        bot.send_message(message.chat.id, text="Все данные о вас успешно очищены")

bot.polling(none_stop=True)
