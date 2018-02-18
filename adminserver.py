import boto3
from boto3.dynamodb.conditions import Attr
import datetime
import time
from calendar import timegm
from flask import Flask, render_template, request, session, redirect
import os
import hashlib
import json
from time import sleep
import threading
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from gpiozero import Buzzer

bz = Buzzer(26)
kitchentemp = 25.0
drinktemp = 25.0
kitchenalarm = False
drinkalarm = False

host = "a1gshwfs8ne6l4.iot.us-west-2.amazonaws.com"
rootCAPath = "rootca.pem"
certificatePath = "certificate.pem.crt"
privateKeyPath = "private.pem.key"


def customCallback(client, userdata, message):
    global drinktemp
    j = json.loads(message.payload)
    drinktemp = j['temperature']

def customCallback2(client, userdata, message):
    global kitchentemp
    j = json.loads(message.payload)
    kitchentemp = j['temperature']

def customCallback3(client, userdata, message):
    global kitchenalarm
    j = json.loads(message.payload)
    kitchenalarm = j['isalarm']

def customCallback4(client, userdata, message):
    global drinkalarm
    j = json.loads(message.payload)
    drinkalarm = j['isalarm']

    
my_rpi = AWSIoTMQTTClient("basicPubSub")
my_rpi.configureEndpoint(host, 8883)
my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi.connect()
my_rpi.subscribe("sensors/dhtdrink", 1, customCallback)
my_rpi.subscribe("sensors/dhtfood", 1, customCallback2)
my_rpi.subscribe("firealarm/iskitchenalarm", 1, customCallback3)
my_rpi.subscribe("firealarm/isdrinkalarm", 1, customCallback4)
sleep(2)


# Get the service resource.
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('orders')
usertable = dynamodb.Table('users')

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route("/",methods=['POST', 'GET'])
def login():
    error = ""
    if request.method == 'POST':
        response = usertable.scan()
        item = response['Items']
        for a in item:
            if request.form['username']==a['username'] and hashlib.md5(request.form['password']).hexdigest()==a['password']:
                session['user']=request.form['username']
                return redirect("/profit")
            else:
                error = "Invalid username or password!"
    return render_template("login.html", datapython=error)

@app.route("/logout")
def logout():
    session.pop('user',None)
    return redirect("/")

@app.route("/history")
def history():
    if 'user' in session:
        data=[]
        response = table.scan()
        item = response['Items']
        for a in item:
            data.append([a['timestamp'], a['orderid'], a['food'], a['foodquantity'], a['sides'], a['sidesquantity'], a['drink'], a['drinkquantity'], '$'+a['profit']])

        return render_template("history.html", datapython=data)
    else:
        return redirect("/")


def addtodict(key, value, profitdict):
    if key in profitdict:
        profitdict[key]=profitdict[key]+value
    else:
        profitdict[key]=value
            
@app.route("/profit")
def profit():
    if 'user' in session:
        data=[]
        profit = {'00:00':0,'01:00':0,'02:00':0,'03:00':0,'04:00':0,'05:00':0,'06:00':0,'07:00':0,'08:00':0,'09:00':0,'10:00':0,'11:00':0,'12:00':0,'13:00':0,'14:00':0,'15:00':0,'16:00':0,'17:00':0,'18:00':0,'19:00':0,'20:00':0,'21:00':0,'22:00':0,'23:00':0}
        response = table.scan()
        item = response['Items']
        for a in item:
            d = datetime.datetime.strptime(a['timestamp'], '%Y-%m-%d %H:%M:%S.%f').replace(microsecond=0,second=0,minute=0)
            stringdate = d.strftime('%H:%M')
            if d > datetime.datetime.today() + datetime.timedelta(days = -1):
                addtodict(stringdate, float(a['profit']), profit)
        for b in sorted(profit):
            data.append([b, '{:.2f}'.format(profit[b])])

        #to show the time now at the end
        now = datetime.datetime.now()
        sorteddata=data[now.hour+1:]
        sorteddata+=data[:now.hour+1]
        return render_template("profit.html", datapython=sorteddata)
    else:
        return redirect("/")

@app.route("/count")
def count():
    if 'user' in session:
        data=[]
        count = {'00:00':0,'01:00':0,'02:00':0,'03:00':0,'04:00':0,'05:00':0,'06:00':0,'07:00':0,'08:00':0,'09:00':0,'10:00':0,'11:00':0,'12:00':0,'13:00':0,'14:00':0,'15:00':0,'16:00':0,'17:00':0,'18:00':0,'19:00':0,'20:00':0,'21:00':0,'22:00':0,'23:00':0}
        response = table.scan()
        item = response['Items']
        for a in item:
            d = datetime.datetime.strptime(a['timestamp'], '%Y-%m-%d %H:%M:%S.%f').replace(microsecond=0,second=0,minute=0)
            stringdate = d.strftime('%H:%M')
            if d > datetime.datetime.today() + datetime.timedelta(days = -1):
                addtodict(stringdate, 1, count)
        for b in sorted(count):
            data.append([b, count[b]])

        #to show the time now at the end
        now = datetime.datetime.now()
        sorteddata=data[now.hour+1:]
        sorteddata+=data[:now.hour+1]
        return render_template("count.html", datapython=sorteddata)
    else:
        return redirect("/")

@app.route("/firealarm")
def firealarm():
    global kitchentemp
    global drinktemp
    global kitchenalarm
    global drinkalarm
    if 'user' in session:
        global firealarm
        return render_template("fire.html", datapython=[kitchentemp, drinktemp, kitchenalarm, drinkalarm])
    else:
        return redirect("/")

@app.route("/kitchenoff")
def kitchenoff():
    if 'user' in session:
        global kitchentemp
        global drinktemp
        global kitchenalarm
        global drinkalarm
        kitchenalarm = False
        send_message = {'alarm':kitchenalarm}
        my_rpi.publish("firealarm/kitchen", json.dumps(send_message), 1)
        return render_template("fire.html", datapython=[kitchentemp, drinktemp, kitchenalarm, drinkalarm])
    else:
        return redirect("/")

@app.route("/kitchenon")
def kitchenon():
    if 'user' in session:
        global kitchentemp
        global drinktemp
        global kitchenalarm
        global drinkalarm
        kitchenalarm = True
        send_message = {'alarm':kitchenalarm}
        my_rpi.publish("firealarm/kitchen", json.dumps(send_message), 1)
        return render_template("fire.html", datapython=[kitchentemp, drinktemp, kitchenalarm, drinkalarm])
    else:
        return redirect("/")

@app.route("/drinkoff")
def drinkoff():
    if 'user' in session:
        global kitchentemp
        global drinktemp
        global kitchenalarm
        global drinkalarm
        drinkalarm = False
        send_message = {'alarm':drinkalarm}
        my_rpi.publish("firealarm/drink", json.dumps(send_message), 1)
        return render_template("fire.html", datapython=[kitchentemp, drinktemp, kitchenalarm, drinkalarm])
    else:
        return redirect("/")

@app.route("/drinkon")
def drinkon():
    if 'user' in session:
        global kitchentemp
        global drinktemp
        global kitchenalarm
        global drinkalarm
        drinkalarm = True
        send_message = {'alarm':drinkalarm}
        my_rpi.publish("firealarm/drink", json.dumps(send_message), 1)
        return render_template("fire.html", datapython=[kitchentemp, drinktemp, kitchenalarm, drinkalarm])
    else:
        return redirect("/")

    
if __name__ =='__main__':
    app.run(debug=False, host='0.0.0.0', port=5001)
