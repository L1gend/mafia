from random import choice
from telebot import TeleBot
import db
from time import sleep

TOKEN = '6346327718:AAGCUYdfXojRdWXl2JByQ6qcfYLVRwrz9RI'
bot = TeleBot(TOKEN)
game = False
night = False
global sheriff_vote
sheriff_vote = 0

def game_loop(message):
    global night
    bot.send_message(message.chat.id, 'Добро пожаловать в игру, вам дается 2 минуты чтобы познакомиться')
    sleep(120)
    x = 2
    while True:
        if night:
            bot.send_message(message.chat.id, 'Город засыпает, мафия проспается, шериф ищет мафию')
            bot.send_message(message.chat.id, get_killed)
        else:
            bot.send_message(message.chat.id, 'Наступил день, город просыпается')
            bot.send_message(message.chat.id, get_killed)
        winner = db.check_winner()
        if winner is not None:
            bot.send_message(message.chat.id, f'Победили {winner}')
            break
        night = not night
        alive = db.get_all_alive()
        alive = '\n'.join(alive)
        bot.send_message(message.chat.id, f'Остались в игре: {alive}')
        db.clear()
        sleep(120)

@bot.message_handler(commands=['play'])
def start(message):
    bot.send_message(message.chat.id, 'Если хотите играть, напишите "готов играть" мне в лс')

@bot.message_handler (func=lambda message: message.text.lower() == 'готов играть' and message.chat.type == 'private')
def add_players(message):
    db.insert_player(message.from_user.id, message.from_user.username)
    bot.send_message(message.chat.id, f'{message.from_user.username} играет')
    bot.send_message(message.chat.id, username=message.from_user.username)

@bot.message_handler(commands=['game'])
def start_game(message):
    global game
    players = db.players_amount()
    if players >= 5:
        db.set_roles(players)
        game = True
        players_roles = db.get_player_roles()
        mafias = db.get_mafia_usernames()
        for players_id, role in players_roles:
            bot.send_message(players_id, f'Мафия: {mafias}')
        bot.send_message(message.chat.id, 'Игра началась')
        game_loop(message)
        db.clear(dead=True)
        return
    bot.send_message(message.chat.id, 'Недостаточно игроков')

def get_killed(night):
    if night:
        killed = db.mafia_kill()
        return f'Мафия убила {killed}'
    killed = db.citizen_kill()

@bot.message_handler(commands=['kick'])
def kick(message):
    username = message.text.split()[1:]
    usernames = db.get_all_alive()
    if not night:
        if not username in usernames:
            bot.send_message(message.chat.id, 'Такого пользователя нет в игре')
            return
        voted = db.vote('citizen_vote', username, message.from_user.id)
        if voted:
            bot.send_message(message.chat.id, 'Ваш голос учтен')
            return
        bot.send_message(message.chat.id, 'Вы не можете голосовать')
        return
    bot.send_message(message.chat.id, 'Сейчас ночь! Нельзя голосовать')

@bot.message_handler(commands=['kill'])
def kill(message):
    username = message.text.split()[1:]
    usernames = db.get_all_alive()
    mafia = db.get_mafia_usernames()
    if night:
        if message.from_user.username not in mafia:
            bot.send_message(message.chat.id, 'Вы не мафия!')
            return
        if not username in usernames:
            bot.send_message(message.chat.id, 'Такого пользователя нет в игре')
            return
        voted = db.vote('mafia_vote', username, message.from_user.id)
        if voted:
            bot.send_message(message.chat.id, 'Ваш голос учтен')
            return
        bot.send_message(message.chat.id, 'Вы не можете голосовать')
        return
    bot.send_message(message.chat.id, 'Сейчас день! Нельзя голосовать')

@bot.message_handler(commands=['check'])
def check(message):
    username = message.text.split()[1:]
    usernames = db.get_all_alive()
    mafia = db.get_mafia_usernames()
    sheriff = db.get_sheriff_username()
    if night:
        if message.from_user.username not in sheriff:
            bot.send_message(message.chat.id, 'Вы не шериф!')
            return
        if not username in usernames:
            bot.send_message(message.chat.id, 'Такого пользователя нет в игре')
            return
        if sheriff_vote == 0:
            bot.send_message(message.chat.id, 'Вы уже проверяли')
            return
        if username in mafia:
            bot.send_message(message.chat.id, 'Данный игрок мафия')
            sheriff_vote = 1
            return
        bot.send_message(message.chat.id, 'Данный игрок не мафия')
        sheriff_vote = 1
        return
    bot.send_message(message.chat.id, 'Сейчас не ночь, нельзя проверять')
        

if __name__ == '__main__':
    bot.polling(none_stop=True)
