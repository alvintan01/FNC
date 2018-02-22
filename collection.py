from flask import Flask, render_template, request
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
from gpiozero import Buzzer
import json

foodorderid=[]
drinkorderid=[]
currentorderid=""
pastservedorderid=[]
bz = Buzzer(26)

# Custom MQTT message callback
def customCallback(client, userdata, message):
    global foodorderid
    global drinkorderid
    global currentorderid
    global pastservedorderid
    j = json.loads(message.payload)
    if j['orderid'] in drinkorderid:
            bz.on()
            sleep(0.5)
            bz.off()
            sleep(0.5)
            drinkorderid.remove(j['orderid'])
            if currentorderid!="":
                pastservedorderid.append(currentorderid)
            currentorderid=j['orderid']
    else:
        foodorderid.append(j['orderid'])
    

def customCallback2(client, userdata, message):
    global foodorderid
    global drinkorderid
    global currentorderid
    global pastservedorderid
    j = json.loads(message.payload)
    if j['orderid'] in foodorderid:
            bz.on()
            sleep(0.5)
            bz.off()
            sleep(0.5)
            foodorderid.remove(j['orderid'])
            if currentorderid!="":
                pastservedorderid.append(currentorderid)
            currentorderid=j['orderid']
    else:
        drinkorderid.append(j['orderid'])
    
host = "a1gshwfs8ne6l4.iot.us-west-2.amazonaws.com"
rootCAPath = "rootca.pem"
certificatePath = "certificate.pem.crt"
privateKeyPath = "private.pem.key"

my_rpi = AWSIoTMQTTClient("firestation")
my_rpi.configureEndpoint(host, 8883)
my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi.connect()
my_rpi.subscribe("orders/foodcompleted", 1, customCallback)
my_rpi.subscribe("orders/drinkcompleted", 1, customCallback2)


app = Flask(__name__)

@app.route("/")
def main():
    global currentorderid
    global pastservedorderid
    pastservedorderid=pastservedorderid[-5:]
    return render_template("collection.html", datapython=[currentorderid,pastservedorderid[::-1]])

if __name__ =='__main__':
    app.run(debug=False, host='0.0.0.0', port=5002)

while True:
    sleep(5)


