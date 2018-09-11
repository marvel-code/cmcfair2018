#!/usr/bin/env python
import telebot
from telebot import apihelper
import re
import cfg
import time
from peewee import *


# SETTINGS


apihelper.proxy = cfg.proxy
team_game_interval = 5 # Время в минутах, которое должно пройти команды для опр-ой КП


# DATA


current_game_id = 0 # TODO: привязать к id чата

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


@bot.message_handler(commands=['help'])
def send_manual(message):
	msg = 'Руководоство по боту:\n'

	msg += '\n/games_list — список доступных игр'
	msg += '\n/select_game <id> — выбрать игру'
	msg += '\n<team> <score> [f] — назначить `score` очков для команды `team`. \
	Если f==1, то назначить принудительно'

	bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['games_list'])
def send_games_list(message):
	msg = 'Список игр:\n\n'

	for i in range(1, games_count + 1):
		msg += '{} — {}\n'.format(i, games_names[i])

	bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['select_game'])
def set_game(message):
	msg = ''

	global current_game_id
	try:
		current_game_id = int(re.findall(r'\d+', message.text)[0])
		msg = 'Вы выбрали игру №{} \'{}\''.format(current_game_id, games_names[current_game_id])

	except Exception as ex:
		msg = 'Ошибочка :-('
		print(ex)

	bot.send_message(message.chat.id, msg)




@bot.message_handler(regexp='^\d+ +\d+ *\d?$')
def process_game(message):
	msg = ''

	global current_game_id
	if current_game_id == 0:
		msg = 'Вы не назначили игру. Наберите следующую команду:\n/set_game id'

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
				else:
					if old_score >= new_score and not is_forcibly:
						if old_score == new_score:
							msg = 'Ничего не изменилось.'
						else:
							msg = 'В этот раз похуже. Старайтесь лучше!'

					elif new_score > 10 and not is_forcibly:
						msg = 'Счёт не может быть больше 10'

					else:
						msg = 'Поздравляем, счёт увеличился!'
						# Update team score for this game
						if is_forcibly:
							msg = 'Принудительное изменение счёта.'
						game_data[0] = str(new_score)
						game_data[1] = str(int(time.time()))
						team_data[current_game_id - 1] = ','.join(game_data)
						t.data = ';'.join(team_data)
						t.save()

				msg += '\n\nСчёт {} команды равен {}'.format(team_id, game_data[0])

		except IndexError as ex:
			msg = 'Ошибочка :-('
			print(ex)


	bot.send_message(message.chat.id, msg)


# LAUNCH


print('Launched')
bot.polling()
