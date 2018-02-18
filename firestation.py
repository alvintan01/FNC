from flask import Flask, render_template, request
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
import json

temperature = 25.0
kitchentemperature =25.0

# Custom MQTT message callback
def customCallback(client, userdata, message):
    global temperature
    j = json.loads(message.payload)
    temperature = j['temperature']

def customCallback2(client, userdata, message):
    global kitchentemperature
    j = json.loads(message.payload)
    kitchentemperature = j['temperature']
    
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
my_rpi.subscribe("sensors/dhtdrink", 1, customCallback)
my_rpi.subscribe("sensors/dhtfood", 1, customCallback2)


app = Flask(__name__)

@app.route("/")
def main():
    global temperature
    global kitchentemperature
    return render_template("firestation.html", datapython=[temperature,kitchentemperature])

if __name__ =='__main__':
    app.run(debug=False, host='0.0.0.0', port=5002)

while True:
    sleep(5)


