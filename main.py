#!/usr/bin/env python
import telebot
from telebot import apihelper
import re
import cfg
import time
from peewee import *


# SETTINGS


apihelper.proxy = cfg.proxy
password4auth = cfg.password4auth
team_game_interval = 5 # Время в минутах, которое должно пройти команды для опр-ой КП
deny_message = 'Упс. Ты кто? Я тебя не пускаю.'


# DATA


chats_games_ids = {}
authed = {}

games_count = 19
games_names = {
	1: 'Наступательное движение',
	2: 'kp2',
	3: 'kp3',
	4: 'kp4',
	5: 'kp5',
	6: 'kp6',
	7: 'kp7',
	8: 'kp8',
	9: 'kp9',
	10: 'kp10',
	11: 'kp11',
	12: 'kp12',
	13: 'kp13',
	14: 'kp14',
	15: 'kp15',
	16: 'kp16',
	17: 'kp17',
	18: 'kp18',
	19: 'kp19',
}

db = SqliteDatabase('teams.db')
class Team(Model):
    number = IntegerField(3, primary_key=True, unique=True)
    data = CharField(512)

    class Meta:
        database = db


# MAIN


bot = telebot.TeleBot(cfg.token)


def get_current_game_id(chat_id):
	current_game_id = 0
	try:
		current_game_id = chats_games_ids[chat_id]
	except:
		pass

	return current_game_id

def extract_arg(arg):
	return arg.split()[1:]

@bot.message_handler(commands=['start'])
def send_welcome(message):
	msg = 'Приветствуем на Ярмарке ВМК 2018!\nЧтобы узнать функции бота, наберите команду /help\n'

	bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['auth'])
def auth(message):
	msg = ''

	password = extract_arg(message.text)[0]
	global password4auth
	result = password == password4auth
	authed.update({message.chat.id: result})

	if result:
		msg = 'Главное, никого не обижай :) Удачи!'
	else:
		msg = deny_message

	bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['help'])
def send_manual(message):
	if list(authed.keys()).count(message.chat.id) == 0 or not authed[message.chat.id]:
		bot.send_message(message.chat.id, deny_message)
		return

	msg = 'Руководоство по боту:'

	msg += '\n\n/games_list — список доступных игр'
	msg += '\n\n/select_game <id> — выбрать игру'
	msg += '\n\n/game_stat — статистика текущей игры'
	msg += '\n\n<team> <score> [f] — назначить `score` очков для команды `team`. \
	Если f==1, то назначить принудительно'

	bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['games_list'])
def send_games_list(message):
	if list(authed.keys()).count(message.chat.id) == 0 or not authed[message.chat.id]:
		bot.send_message(message.chat.id, deny_message)
		return

	msg = 'Список игр:\n\n'

	for i in range(1, games_count + 1):
		msg += '{} — {}\n'.format(i, games_names[i])

	bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['select_game'])
def set_game(message):
	if list(authed.keys()).count(message.chat.id) == 0 or not authed[message.chat.id]:
		bot.send_message(message.chat.id, deny_message)
		return

	msg = ''

	global chats_games_ids
	try:
		game_id = int(re.findall(r'\d+', message.text)[0])
		chats_games_ids.update({message.chat.id: game_id})
		msg = 'Вы выбрали игру №{} \'{}\''.format(game_id, games_names[game_id])

	except Exception as ex:
		msg = 'Ошибочка :-('
		print(ex)

	bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['game_stat'])
def send_game_stat(message):
	if list(authed.keys()).count(message.chat.id) == 0 or not authed[message.chat.id]:
		bot.send_message(message.chat.id, deny_message)
		return

	current_game_id = get_current_game_id(message.chat.id)

	if current_game_id == 0:
		bot.send_message(message.chat.id, 'Выберите игру через /select_game <id>')
		return

	msg = 'Статистика по игре №{} \'{}\':\n'.format(current_game_id, games_names[current_game_id])
	teams = Team.select()
	for t in teams:
		team_data = t.data.split(';')
		if len(team_data) < games_count:
			team_data = ('0,0' + ';0,0' * (games_count - 1)).split(';')
		game_data = team_data[current_game_id - 1].split(',') # [0] score [1] last_time
		score = int(game_data[0])
		team_delta = time.time() - float(game_data[1])

		msg += '\n{} — {}. Ждать {}мин {}с'.format(t.number, score, int(team_game_interval - team_delta / 60) if team_delta < team_game_interval * 60 else 0, 60 - int(team_delta % 60)  if team_delta < team_game_interval * 60 else 0)

	bot.send_message(message.chat.id, msg)



@bot.message_handler(regexp='^\d+ +\d+ *\d?$')
def process_game(message):
	if list(authed.keys()).count(message.chat.id) == 0 or not authed[message.chat.id]:
		bot.send_message(message.chat.id, deny_message)
		return

	msg = ''

	global chats_games_ids
	current_game_id = get_current_game_id(message.chat.id)

	if current_game_id == 0:
		msg = 'Вы не назначили игру. Список игр: /games_list. Выбрать игру:\n/select_game id'

	else:
		args = re.findall(r'\w+', message.text)
		team_id = int(args[0])
		new_score = int(args[1])
		is_forcibly = len(args) > 2 and int(args[2]) == 1

		try:
			t = Team.get(Team.number == team_id)
			if not t:
				msg = 'Неправильный номер команды'

			else:
				# Get team data for this game
				team_data = t.data.split(';')
				if len(team_data) < games_count:
					team_data = ('0,0' + ';0,0' * (games_count - 1)).split(';')
				game_data = team_data[current_game_id - 1].split(',') # [0] score [1] last_time
				old_score = int(game_data[0])
				team_delta = time.time() - float(game_data[1])

				# Check for time rule
				if team_delta / 60 < team_game_interval and not is_forcibly:
					msg += 'Прошло мало времени. Осталось {}мин {}с'.format(int(team_game_interval - team_delta / 60), 60 - int(team_delta % 60))
					new_score = old_score

				else:
					if old_score >= new_score and not is_forcibly:
						if old_score == new_score:
							msg = 'Ничего не изменилось.'
						else:
							msg = 'В этот раз похуже. Старайтесь лучше!'
							new_score = old_score

					elif new_score > 10 and not is_forcibly:
						msg = 'Счёт не может быть больше 10'
						new_score = old_score

					else:
						msg = 'Поздравляем, счёт увеличился!'
						if is_forcibly:
							msg = 'Принудительное изменение счёта.'

					# Update team score and time for this game
					game_data[0] = str(new_score)
					game_data[1] = str(int(time.time()))
					team_data[current_game_id - 1] = ','.join(game_data)
					t.data = ';'.join(team_data)
					t.save()

				if new_score != old_score:
					msg += '\n\nСчёт {} команды поменялся с {} на {}'.format(team_id, old_score, new_score)
				else:
					msg += '\n\nСчёт {} команды остался равен {}'.format(team_id, old_score)

		except IndexError as ex:
			msg = 'Ошибочка :-('
			print(ex)


	bot.send_message(message.chat.id, msg)


# LAUNCH


print('Launched')
bot.polling()
