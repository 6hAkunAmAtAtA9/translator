import telebot
import psycopg2
import random
from telebot import types
import datetime

TOKEN = ''
bot = telebot.TeleBot(TOKEN)
connection = psycopg2.connect(dbname="translator",
                              user="postgres",
                              password="chalox", host="192.168.1.102")
cursor = connection.cursor()

global active_users
active_users = {}

# @bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.chat.id not in active_users.keys())
def start(message):
    print(f'Start of start function')
    cursor.execute(
        f'''
        select *
        from main.words
        '''
    )

    question = cursor.fetchall()
    active_users[message.chat.id] = {'ids': list(range(len(question))),
                                     'words': [x[0] for x in question],
                                     'trans': [x[1] for x in question],
                                     }
    send_question(message)

def send_question(message):
    # print(f'Sending message {active_users}')
    current_id = random.choice(active_users[message.chat.id]['ids'])
    current_word = active_users[message.chat.id]['words'][current_id]
    current_answer = active_users[message.chat.id]['trans'][current_id]

    current_variants = [current_answer,
                     active_users[message.chat.id]['trans'][random.choice(active_users[message.chat.id]['ids'])],
                     active_users[message.chat.id]['trans'][random.choice(active_users[message.chat.id]['ids'])],
                     active_users[message.chat.id]['trans'][random.choice(active_users[message.chat.id]['ids'])]]
    random.shuffle(current_variants)
    active_users[message.chat.id]['current_word'] = current_word
    active_users[message.chat.id]['current_answer'] = current_answer
    active_users[message.chat.id]['current_variants'] = current_variants
    bot.send_message(message.chat.id, current_word, reply_markup=get_keyboard(current_variants))

def get_keyboard(current_variants):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for option in current_variants:
        markup.add(option)
    return markup

@bot.message_handler(func=lambda message: True)
def check_answer(message):
    user_answer = message.text
    if user_answer == active_users[message.chat.id]['current_answer']:
        pass
    else:
        bot.send_message(message.chat.id, f"Неправильно. Правильный ответ: {active_users[message.chat.id]['current_answer']}")

    insert_query = '''
        INSERT INTO main.answers (id, event_date, word, is_correct)
        VALUES (%s, %s, %s, %s)
    '''
    cursor.execute(insert_query, (message.chat.id,
                                  datetime.datetime.now(),
                                  active_users[message.chat.id]['current_word'],
                                  user_answer == active_users[message.chat.id]['current_answer']))
    connection.commit()

    send_question(message)

bot.polling(none_stop=True)