import telebot
from telebot import types
import threading
import time
import urllib
import requests
from lxml import html
import sqlite3


conexion = sqlite3.connect('db_tasa_itala', check_same_thread=False)
cursor = conexion.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS tasas (ultima_tasa varchar(50) )")
cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (id_usuario varchar(50) unique)") 

API_TOKEN = '864289740:AAFSutec8On7FdI5A6y3esd980LcO-p6D2Y'
bot = telebot.TeleBot(API_TOKEN)




def insertar(precio):
	try:
		lock.acquire(True)
		cursor.execute("INSERT INTO tasas (ultima_tasa) VALUES (?)",(str(precio),))
		cursor.execute("UPDATE tasas SET ultima_tasa=?",(str(precio),))

	finally:
		lock.release()


def actualizar(precio):
	try:
		lock.acquire(True)
		cursor.execute("UPDATE tasas SET ultima_tasa=?",(str(precio),))

	finally:
		lock.release()

def get_price():
	try:
		lock.acquire(True)
		datos = cursor.execute("SELECT * FROM tasas")
		dato = datos.fetchone()
		if dato:
			print(dato[0])
		else:
			dato = ['']
	finally:
		lock.release()
	return str(dato[0])



def notificar():
	print('Enviando notificacion a todos los usuarios')
	try:
		lock.acquire(True)
		datos = cursor.execute("SELECT * FROM usuarios")
		datos = datos.fetchall()

	finally:
		lock.release()

	if datos:
		for i in datos:
			print('Notificando a: ' + str(i[0]))
			bot.send_message(str(i[0]),'Nueva tasa:\n'+get_price())
	else:
		print('Error.')

def update_last_price():

	while True:
		page = requests.get('https://app.cambiositalo.com/peru/')
		tree = html.fromstring(page.content.decode("utf8"))
		precio = tree.xpath('//*[@id="envios-a-venezuela"]/div[2]/div[3]/div[1]/div/div/div[5]/div/p/strong[1]/span')
		precio = str(precio[0].text)

		if get_price() != precio and get_price() != '':
			notificar()

		if get_price() == '':
			insertar(precio)
		else:
			actualizar(precio)

		time.sleep(1)



@bot.message_handler(commands=['start'])
def send_welcome(message):    
	bot.send_message(message.from_user.id, "Hola "+message.from_user.first_name+" la tasa hoy es \n <b>"+get_price()+"</b>\nTe avisare cuando cambie!",parse_mode='HTML')

	try:
		lock.acquire(True)
		cursor.execute("INSERT or IGNORE INTO usuarios (id_usuario) VALUES (?)",(str(message.from_user.id),))

	finally:
		lock.release()

@bot.message_handler(func=lambda message: True)
def echo_message(message):
	bot.send_message(message.from_user.id, get_price())



lock = threading.Lock()

t1 = threading.Thread(name="consulta tasa", target=update_last_price)
t1.start()


bot.polling()

conexion.commit()
conexion.close()


