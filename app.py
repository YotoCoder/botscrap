import os
import sys
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

API_TOKEN = os.environ.get("SECRET_KEY")
bot = telebot.TeleBot(API_TOKEN)

dato = ''

lock = threading.Lock()





def menu():
    markup = types.ReplyKeyboardMarkup(row_width=1)
    itembtn1 = types.KeyboardButton('Consultar tasa')
    markup.add(itembtn1) 
    
    return markup

def test():
    try:
    	lock.acquire()
    	cursor.execute("UPDATE tasas SET ultima_tasa=?",('str(precio)',))
    	conexion.commit()
    finally:
    	lock.release()
    
def insertar(precio):
	try:
		lock.acquire(True)
		cursor.execute("INSERT INTO tasas (ultima_tasa) VALUES (?)",(str(precio),))
		cursor.execute("UPDATE tasas SET ultima_tasa=?",(str(precio),))
		conexion.commit()

	finally:
		lock.release()


def actualizar(precio):
	try:
		lock.acquire(True)
		cursor.execute("UPDATE tasas SET ultima_tasa=?",(str(precio),))
		conexion.commit()
	finally:
		lock.release()

def get_price():
	global dato
	try:
		lock.acquire(True)
		datos = cursor.execute("SELECT * FROM tasas")
		dato = datos.fetchone()
		if dato:
			pass
      
		else:
			dato = ['']
	except Exception as e:
		#print('\n\nEstamos en get_price \nUps.. '+ str(e)+'\n\n')
		#sys.exit()
		pass
	finally:
		lock.release()

	return str(dato[0])



def notificar(precionuevo):

	try:
		lock.acquire(True)
		datos = cursor.execute("SELECT * FROM usuarios")
		datos = datos.fetchall()

	finally:
		lock.release()

	if datos:
		for i in datos:
			#print('Notificando a: ' + str(i[0]))
			bot.send_message(str(i[0]),'Nueva Tasa:\n'+precionuevo)
	else:
		#print('Error.')
		pass

def update_last_price():

	while True:
		try:
			page = requests.get('https://app.cambiositalo.com/peru/')
			if page.status_code == 200:
				tree = html.fromstring(page.content.decode("utf8"))
				precio = tree.xpath('//*[@id="envios-a-venezuela"]/div[2]/div[3]/div[1]/div/div/div[5]/div/p/strong[1]/span')
				precio = str(precio[0].text)
			else:
				precio = get_price()
		except Exception as e:
			precio = get_price()



		try:
			if get_price() != precio and get_price() != '':
				notificar(precio)

			if get_price() == '':
				insertar(precio)
			else:
				actualizar(precio)

		except Exception as e:
			#print('Estamos en update_last_price \nUps.. '+ str(e)+'\n\n')
			#sys.exit()
			#t1.join()
			pass

		time.sleep(60)



@bot.message_handler(commands=['start'])
def send_welcome(message):    
	bot.send_message(message.from_user.id, "Hola "+message.from_user.first_name+" la tasa hoy es \n <b>"+get_price()+"</b>\nTe avisare cuando cambie!",reply_markup=menu(),parse_mode='HTML')

	try:
		lock.acquire(True)
		cursor.execute("INSERT or IGNORE INTO usuarios (id_usuario) VALUES (?)",(str(message.from_user.id),))
		conexion.commit()

	finally:
		lock.release()

@bot.message_handler(func=lambda message: True)
def echo_message(message):

	if message.text == 'Test':
		t2 = threading.Thread(name="test", target=test)
		t2.start()
		t2.join()
	else:

		bot.send_message(message.from_user.id, get_price())

	try:
		lock.acquire(True)
		cursor.execute("INSERT or IGNORE INTO usuarios (id_usuario) VALUES (?)",(str(message.from_user.id),))
		conexion.commit()

	finally:
		lock.release()


t1 = threading.Thread(name="consulta tasa", target=update_last_price)
t1.start()

bot.polling()

conexion.commit()
conexion.close()


