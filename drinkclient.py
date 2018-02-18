from flask import Flask, render_template, request
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
import json
from gpiozero import Button, Buzzer
import MySQLdb
import Adafruit_DHT
import threading

button = Button(13, pull_up=False)
bz = Buzzer(26)
timestamp = ""
firealarm = False

try:
    db = MySQLdb.connect("localhost", "ca2user", "password", "orders")
    curs = db.cursor()
    print("Successfully connected to database!")
except:
    print("Error connecting to mySQL database")

# Custom MQTT message callback
def customCallback(client, userdata, message):
	bz.on()
	sleep(0.5)
	bz.off()
	j = json.loads(message.payload)
        db = MySQLdb.connect("localhost", "ca2user", "password", "orders")
        curs = db.cursor()
	sql = "INSERT into drinkorders VALUES ('"+str(j['orderid'])+"','"+str(j['drink'])+"','"+str(j['drinkquantity'])+"','"+str(j['timestamp'])+"',False)"
        curs.execute(sql)
        db.commit()
        curs.close()
        db.close()

def customCallback2(client, userdata, message):
    global firealarm
    j = json.loads(message.payload)
    firealarm = j['alarm']

def deleteOrder():
        global timestamp
        db = MySQLdb.connect("localhost", "ca2user", "password", "orders")
        curs = db.cursor()
        sql = "Update drinkorders set completed=True where timestamp='"+timestamp+"'"
        curs.execute(sql)
        db.commit()
        curs.close()
        db.close()
		
button.when_pressed = deleteOrder

host = "a1gshwfs8ne6l4.iot.us-west-2.amazonaws.com"
rootCAPath = "rootca.pem"
certificatePath = "certificate.pem.crt"
privateKeyPath = "private.pem.key"

my_rpi = AWSIoTMQTTClient("drinkclient")
my_rpi.configureEndpoint(host, 8883)
my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi.connect()
my_rpi.subscribe("order/drink", 1, customCallback)
my_rpi.subscribe("firealarm/drink", 1, customCallback2)


app = Flask(__name__)



# Publish to the same topic in a loop forever
def run():
    global firealarm
    while True:
            humidity, temperature = Adafruit_DHT.read_retry(11, 4)
            send_message = {'temperature':temperature}
            if (temperature > 30):
                firealarm = True
                message = {'isalarm': firealarm}
                my_rpi.publish("firealarm/isdrinkalarm", json.dumps(message), 1)
                my_rpi.publish("email/fire", "The fire alarm has been triggered in the drink station.", 1)
            my_rpi.publish("sensors/dhtdrink", json.dumps(send_message), 1)
            sleep(3)

try:
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
except Exception as e:
    print e

def soundbuzzer():
    global firealarm
    while True:
        if firealarm:
            bz.on()
            sleep(0.5)
            bz.off()
            sleep(0.5)
        else:
            sleep(0.5)

try:
    t = threading.Thread(target=soundbuzzer)
    t.daemon = True
    t.start()
except Exception as e:
    print e


@app.route("/")
def drink():
        global timestamp
        db = MySQLdb.connect("localhost", "ca2user", "password", "orders")
        curs = db.cursor()
        sql = "Select * from drinkorders where completed = False order by orderid"
        curs.execute(sql)
        data = []
        timeset = False
        for (orderid, drink, drinkquantity, ordertimestamp, completed) in curs:
                if not timeset:
                        timestamp=ordertimestamp
                        timeset = True
                data.append([orderid,drink,drinkquantity, ordertimestamp])
        curs.close()
        db.close()
        return render_template("drink.html", datapython=data)

if __name__ =='__main__':
    app.run(debug=False, host='0.0.0.0')

while True:
    sleep(5)


