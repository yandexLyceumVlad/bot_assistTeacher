import datetime

from telegram.ext import Updater, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram.ext import CommandHandler

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode
import telegramcalendar

import schedule
import time

import logging

#from config import TOKEN, log_terminal
import os
from doc import *
from schedule_class import *
from display_schedule_class import *

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

users_events = dict()

NAME_EVENT, DATE_EVENT, TIME_EVENT, LINK_EVENT, COMMENT_EVENT = range(5)

TOKEN = os.environ['TOKEN']
updater = Updater(TOKEN, use_context=True)


dp = updater.dispatcher
jp = updater.job_queue

markup_all_comand = ReplyKeyboardMarkup([['/add', '/today', '/tomorrow', '/all_events']], one_time_keyboard=False)

def start(update, context):
    logging.info("call start")
    text = str(datetime.datetime.now())

    update.message.reply_text(f"Привет! Я помогаю не забывать все на свете)\n {text}",
                              reply_markup=markup_all_comand)


def dialog(update, context):
    logging.info("call dialog")
    text = " ".join([j.name for j in jp.jobs()])
    #text = "Просто *болтаем*?"
    update.message.reply_text(text, parse_mode="Markdown",
                              reply_markup=markup_all_comand)


def help(update, context):
    logging.info("call help")
    help_lines = "Бот для запоминания событий и напоминании о них"
    update.message.reply_text(help_lines, reply_markup=markup_all_comand)

# диалог по добавлению события
def add_conversation_event():
    global dp
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add)],
        states={
            NAME_EVENT: [MessageHandler(Filters.text, add_event_name, pass_user_data=True),
                         MessageHandler(Filters.text, stop)],
            DATE_EVENT: [CallbackQueryHandler(add_event_date_callback),
                         MessageHandler(Filters.text, stop)],
            TIME_EVENT: [MessageHandler(Filters.text, add_event_time, pass_user_data=True),
                         MessageHandler(Filters.text, stop)],
            LINK_EVENT: [MessageHandler(Filters.text, add_event_link, pass_user_data=True),
                         MessageHandler(Filters.text, stop)],
            COMMENT_EVENT: [MessageHandler(Filters.text, add_event_comment, pass_user_data=True),
                            MessageHandler(Filters.text, stop)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    dp.add_handler(conv_handler)

# все функции по добавлению события
def add(update, context):
    logging.info("call add")
    update.message.reply_text("Добавляем в календарь. Если передумал - /stop. \n Как называется, то что надо запомнить?")
    return NAME_EVENT

def add_event_name(update, context):
    logging.info("call add_event_name")
    context.user_data['event_name'] = update.message.text
    update.message.reply_text("Когда это произойдет?",
                              reply_markup=telegramcalendar.create_calendar())
    return DATE_EVENT

def add_event_date_callback(update, context):
    logging.info("call add_event_date_callback")
    selected, date = telegramcalendar.process_calendar_selection(update, context)

    if selected:
        context.user_data['event_date'] = date.date()
    context.bot.send_message(chat_id=update.callback_query.from_user.id,
                             text=date.strftime("%d.%m.%Y") + "\nСкажи в какое это время?",
                             reply_markup=ReplyKeyboardRemove())
    #user_id = update.callback_query.from_user.id
    return TIME_EVENT
    #return ConversationHandler.END

markup_skip = ReplyKeyboardMarkup([['skip']], one_time_keyboard=True)

def add_event_time(update, context):
    try:
        time = datetime.datetime.strptime(update.message.text, "%H:%M").time()
        context.user_data['event_time'] = time
        update.message.reply_text("По какой ссылке нужно будет перейти?",
                                  reply_markup=markup_skip)
        return LINK_EVENT
    except Exception:
        update.message.reply_text(Exception)
        #update.message.reply_text("Неверный формат, пробуем ввести время еще раз")
        return TIME_EVENT


def add_event_link(update, context):
    if update.message.text == 'skip':
        context.user_data['event_link']=""
    else:
        context.user_data['event_link'] = update.message.text
    update.message.reply_text("Еще какие-то уточнения?",
                              reply_markup=markup_skip)
    return COMMENT_EVENT

def add_event_comment(update, context):
    if update.message.text == 'skip':
        context.user_data['event_comment']=""
    else:
        context.user_data['event_comment'] = update.message.text
    user_id = update.message.from_user.id
    create_event(user_id, update, context)
    return ConversationHandler.END

def stop(update, context):
    update.message.reply_text("Как скажешь шеф, все отменяю")
    return ConversationHandler.END


# создаем событие после завершения диалога
def create_event(user_id, update, context):

    event = Display_event(context.user_data['event_name'],
                  context.user_data['event_date'],
                  context.user_data['event_time'],
                  link=context.user_data['event_link'],
                  comment=context.user_data['event_comment'])
    if user_id in users_events:
        logging.info("add event to busy for " + str(user_id))
        users_events[user_id].add_event(event)
    else:
        logging.info("new busy for " +  str(user_id))
        b = Display_busy()
        b.add_event(event)
        users_events[user_id] = b
    update.message.reply_text("Ок, шеф. Я напомню \n\n" + event.display(), parse_mode=ParseMode.MARKDOWN, reply_markup=markup_all_comand)
    when_alarm = (datetime.datetime.combine(event.date, event.time) - datetime.datetime.now()).total_seconds()
    context.job_queue.run_once(callback_alarm, when=when_alarm, context=update.message.chat_id,
                               name="*НАПОМИНАЛКА*\n" + event.display())


def callback_alarm(context):
    logging.info("call callback_alarm")
    context.bot.send_message(chat_id=context.job.context, text=context.job.name, parse_mode=ParseMode.MARKDOWN)

def today_callback_alarm(context):
    logging.info("call today_callback_alarm")
    context.bot.send_message(chat_id=context.job.context, text='BEEP', parse_mode=ParseMode.MARKDOWN)


# все события на сегодня
# должна отображать все события каждое утро в 7 утра (например)
def today(update, context):
    logging.info("call today")
    user_id = update.message.from_user.id
    text = ""
    if user_id in users_events:
        text = "*ВСЕ ДЕЛА НА СЕГОДНЯ*\n" + users_events[user_id].display_today()
    if not text:
        text = "Шеф, до завтра ты абсолютно свободен!"
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# все существующие события
def all_events(update, context):
    logging.info("call all events")
    text = ""
    user_id = update.message.from_user.id
    if user_id in users_events:
        text = "*ВООБЩЕ ВСЕ ДЕЛА*\n" + users_events[user_id].display_all_events()
    if not text:
        text = "Шеф, ты свободен как птица!"
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# все события на завтра
def tomorrow(update, context):
    logging.info("call tomorrow")
    user_id = update.message.from_user.id
    text = ""
    if user_id in users_events:
        text = "*ВСЕ ДЕЛА НА ЗАВТРА*\n" + users_events[user_id].display_tomorrow()
    if not text:
        text = "Шеф, ничего!"
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)



def main():

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("today", today))
    dp.add_handler(CommandHandler("all_events", all_events))
    dp.add_handler(CommandHandler("tomorrow", tomorrow))



    add_conversation_event()

    dp.add_handler(MessageHandler(Filters.text, dialog))
    # dp.add_handler(CommandHandler("set", set_timer,
    #                               pass_args=True,
    #                               pass_job_queue=True,11
    #                               pass_chat_data=True))
    jp.run_daily(today_callback_alarm, time=datetime.time(8,33), context=None, name="today", job_kwargs=None)
    updater.start_polling()
    logging.info("Start bot")
    #schedule.every().day.at("11:42").do(set_timer)
    while True:
        schedule.run_pending()
        time.sleep(1)

    updater.idle()


if __name__ == '__main__':
    main()

