import boto3
from flask import Flask, render_template, request
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
import json
from gpiozero import Button, Buzzer
import MySQLdb
import threading
import Adafruit_DHT
import datetime

dynamodb = boto3.resource('dynamodb')
foodpreparationtime = dynamodb.Table('foodpreparationtime')

button = Button(13, pull_up=False)
bz = Buzzer(26)
timestamp = ""

firealarm = False
currentorderid = ""

# Custom MQTT message callback
def customCallback(client, userdata, message):
	bz.on()
	sleep(0.5)
	bz.off()
	j = json.loads(message.payload)
	db = MySQLdb.connect("localhost", "ca2user", "password", "orders")
        curs = db.cursor()
	sql = "INSERT into foodorders VALUES ('"+str(j['orderid'])+"','"+str(j['food'])+"','"+str(j['foodquantity'])+"','"+str(j['sides'])+"','"+str(j['sidesquantity'])+"', NOW(),False)"
        curs.execute(sql)
        db.commit()
        curs.close()
        db.close()

def customCallback2(client, userdata, message):
    global firealarm
    j = json.loads(message.payload)
    firealarm = j['alarm']
    print firealarm


host = "a1gshwfs8ne6l4.iot.us-west-2.amazonaws.com"
rootCAPath = "rootca.pem"
certificatePath = "certificate.pem.crt"
privateKeyPath = "private.pem.key"

my_rpi = AWSIoTMQTTClient("foodclient")
my_rpi.configureEndpoint(host, 8883)
my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi.connect()
my_rpi.subscribe("order/food", 1, customCallback)
my_rpi.subscribe("firealarm/kitchen", 1, customCallback2)

def deleteOrder():
        global timestamp
        global currentorderid
        global foodpreparationtime
        
        db = MySQLdb.connect("localhost", "ca2user", "password", "orders")
        curs = db.cursor()
        sql = "Update foodorders set completed=True where timestamp='"+timestamp+"'"
        curs.execute(sql)
        db.commit()

        sql = "Select * from foodorders where completed = False and orderid = '"+currentorderid+"'"
        curs.execute(sql)
        if curs.rowcount == 0 and currentorderid!="":
              my_rpi.publish("orders/foodcompleted", json.dumps({'orderid': currentorderid}), 1)
              currentorderid=""
        curs.close()
        db.close()
        try:
               foodpreparationtime.put_item(
                   Item={'timestamp':timestamp, 'time':int((datetime.datetime.now()-datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")).total_seconds())}
                )
        except Exception:
                pass
		
button.when_pressed = deleteOrder


# Publish to the same topic in a loop forever
def run():
    global firealarm
    while True:
            humidity, temperature = Adafruit_DHT.read_retry(11, 4)
            send_message = {'temperature':temperature}
            if (temperature > 30):
                firealarm = True
                message = {'isalarm': firealarm}
                my_rpi.publish("firealarm/iskitchenalarm", json.dumps(message), 1)
                my_rpi.publish("email/fire", "The fire alarm has been triggered in the kitchen.", 1)
            my_rpi.publish("sensors/dhtfood", json.dumps(send_message), 1)
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


app = Flask(__name__)

@app.route("/")
def food():
        global timestamp
        global currentorderid
        db = MySQLdb.connect("localhost", "ca2user", "password", "orders")
        curs = db.cursor()
        sql = "Select * from foodorders where completed = False order by timestamp"
        curs.execute(sql)
        data = []
        timeset = False
        for (orderid, food, foodquantity, sides, sidesquantity, ordertimestamp, completed) in curs:
                if not timeset:
                        timestamp=ordertimestamp
                        currentorderid=orderid
                        timeset = True
                data.append([orderid,food,foodquantity,sides,sidesquantity, ordertimestamp])
        curs.close()
        db.close()
        return render_template("food.html", datapython=data)

if __name__ =='__main__':
    app.run(debug=False, host='0.0.0.0')

while True:
    sleep(5)


