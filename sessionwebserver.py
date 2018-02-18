from flask import Flask, render_template, request, redirect, session
import MFRC522
import datetime
import json
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from rpi_lcd import LCD
import boto3
import os

machineletter="A"
host = "a1gshwfs8ne6l4.iot.us-west-2.amazonaws.com"
rootCAPath = "rootca.pem"
certificatePath = "certificate.pem.crt"
privateKeyPath = "private.pem.key"

my_rpi = AWSIoTMQTTClient("basicPubSub")
my_rpi.configureEndpoint(host, 8883)
my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi.connect()

dynamodb = boto3.resource('dynamodb')
food = dynamodb.Table('food')
sides = dynamodb.Table('sides')
drinks = dynamodb.Table('drinks')
foodlist=[]
drinkslist=[]
sideslist=[]
foodprice={'': 0}
sideprice={'': 0}
drinkprice={'': 0}

#get food
response = food.scan()
item = response['Items']
for a in item:
    foodlist.append([a['name'], a['description'], a['imagelocation']])
    foodprice[a['name']]=float(a['price'])

#get sides
response = sides.scan()
item = response['Items']
for a in item:
    sideslist.append([a['name'], a['description'], a['imagelocation']])
    sideprice[a['name']]=float(a['price'])
    
#get drinks
response = drinks.scan()
item = response['Items']
for a in item:
    drinkslist.append([a['name'], a['description'], a['imagelocation']])
    drinkprice[a['name']]=float(a['price'])

app = Flask(__name__)
app.secret_key = os.urandom(24)

orderid=1
lcd = LCD()
mfrc522 = MFRC522.MFRC522()
continue_reading = True
lcd.text('MasterCard', 1)
lcd.text('Payment', 2)
@app.route("/")
def main():
    return render_template('index.html')

@app.route("/order",methods=['POST', 'GET'])
def selectfood():
    try:
        global continue_reading
        global foodlist
        if 'allorders' not in session:
            session['allorders']=[]
        session['orders']={'Food':'', 'FoodQuantity':0, 'Sides':'', 'SidesQuantity':0, 'Drink':'', 'DrinkQuantity':0, 'RowID':''}
        continue_reading=False
        return render_template('order.html', datapython=foodlist)
    except Exception as e:
        print e
        return redirect("/order") 
        


@app.route("/sides",methods=['POST', 'GET'])
def selectside():
    try:
        global sideslist
        session['orders']={'Food':'', 'FoodQuantity':0, 'Sides':'', 'SidesQuantity':0, 'Drink':'', 'DrinkQuantity':0, 'RowID':''}
        
        if request.method == 'POST':
            if request.form['food']!="":
                session['allorders']=session['allorders']
                session['orders']['Food']=request.form['food']
                session['orders']['FoodQuantity']=1
                session['orders']['RowID']=len(session['allorders'])
            return render_template('order1.html', datapython=sideslist)
    except Exception as e:
        print e
        return redirect("/order") 
    

@app.route("/drinks",methods=['POST', 'GET'])
def selectdrink():
    try:
        global drinkslist
        if request.method == 'POST':
            session['allorders']=session['allorders']
            session['orders']=session['orders']
            session['orders']['Sides']=request.form['sides']
            if not request.form['sides']=="":
                session['orders']['SidesQuantity']=1
            session['orders']['RowID']=len(session['allorders'])
        return render_template('order2.html', datapython=drinkslist)
    except Exception as e:
        print e
        return redirect("/order") 


@app.route("/vieworder",methods=['POST', 'GET'])
def vieworder():
    try:
        if request.method == 'POST':
            session['allorders']=session['allorders']
            session['orders']=session['orders']
            session['orders']['Drink']=request.form['drinks']
            if not request.form['drinks']=="":
                session['orders']['DrinkQuantity']=1
            session['orders']['RowID']=len(session['allorders'])
            if not (session['orders']['Food']=="" and session['orders']['Sides']=="" and session['orders']['Drink']==""):
                cost=float(foodprice[session['orders']['Food']]*int(session['orders']['FoodQuantity']))+float(sideprice[session['orders']['Sides']]*int(session['orders']['SidesQuantity']))+float(drinkprice[session['orders']['Drink']]*int(session['orders']['DrinkQuantity']))
                session['allorders'].append([int(session['orders']['RowID'])+1, session['orders']['Food'],session['orders']['FoodQuantity'],session['orders']['Sides'],session['orders']['SidesQuantity'],session['orders']['Drink'],session['orders']['DrinkQuantity'],session['orders']['RowID'], '{:.2f}'.format(cost)])
                return render_template('orderconfirmation.html', datapython=session['allorders'])
            else:
                return redirect("/order")
    except Exception as e:
        print e
        return redirect("/order") 

@app.route("/updateorder",methods=['POST', 'GET'])
def updateorder():
    if request.method == 'POST':
        session['allorders']=session['allorders']
        try:
            rowid = int(request.form['rowid'])
            operation = request.form['operation']
            if operation=="updatefoodquantity":
                session['allorders'][rowid][2] = request.form['foodquantity']
            elif operation=="updatesidequantity":
                session['allorders'][rowid][4] = request.form['sidequantity']
            elif operation=="updatedrinkquantity":
                session['allorders'][rowid][6] = request.form['drinkquantity']
            elif operation=="delete":
                del session['allorders'][rowid]
                i=0
                j=1
                for a in session['allorders']:
                    a[7]=i#update row id
                    a[0]=j#update item id
                    i=i+1
                    j=j+1
            if len(session['allorders'])!=0:
                session['allorders'][rowid][8] = '{:.2f}'.format(float(foodprice[str(session['allorders'][rowid][1])]*int(session['allorders'][rowid][2]))+float(sideprice[str(session['allorders'][rowid][3])]*int(session['allorders'][rowid][4]))+float(drinkprice[str(session['allorders'][rowid][5])]*int(session['allorders'][rowid][6])))
            
            return render_template('orderconfirmation.html', datapython=session['allorders'])
        except Exception as e:
            print e
            return redirect("/order") 

@app.route("/makepayment",methods=['POST', 'GET'])
def makepayment():
    try:
        global continue_reading
        session['allorders']=session['allorders']
        total = 0
        continue_reading = True
        for a in session['allorders']:
            total+=float(foodprice[str(a[1])]*int(a[2]))+float(sideprice[str(a[3])]*int(a[4]))+float(drinkprice[str(a[5])]*int(a[6]))

        lcd.text('Total Cost:', 1)
        lcd.text('${:.2f}'.format(total), 2)
        return render_template('tap.html', datapython='${:.2f}'.format(total))
    except Exception as e:
        print e
        return redirect("/order") 

@app.route("/scancard",methods=['POST', 'GET'])
def scancard():
    try:
        global continue_reading
        global orderid
        session['allorders']=session['allorders']
        while continue_reading:
            (status,TagType) = mfrc522.MFRC522_Request(mfrc522.PICC_REQIDL)
            # If a card is found
            if status == mfrc522.MI_OK:
                continue_reading=False
                for a in session['allorders']:
                    send_msg = {
                        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                        'orderid': machineletter+str(orderid),
                        'food': a[1],
                        'foodquantity': a[2],
                        'sides': a[3],
                        'sidesquantity': a[4],
                        'drink': a[5],
                        'drinkquantity': a[6],
                        'profit': a[8]#7 is rowid
                    }
                    my_rpi.publish("order/order", json.dumps(send_msg), 1)
                orderid=orderid+1
                session.pop('orders',None)
                session.pop('allorders',None)
                lcd.text('MasterCard', 1)
                lcd.text('Payment', 2)
                return render_template('success.html', datapython=machineletter+str(orderid-1))
    except Exception as e:
        print e
        return redirect("/order") 

@app.route("/success",methods=['POST', 'GET'])
def success():
    try:
        global orderid
        return render_template('tap.html', datapython=orderid-1)
    except Exception as e:
        print e
        return redirect("/order") 

@app.route("/about",methods=['POST', 'GET'])
def about():
    return render_template('about.html')

@app.route("/locate",methods=['POST', 'GET'])
def locate():
    return render_template('location.html')


if __name__ =='__main__':
    app.run(debug=False, host='0.0.0.0')
    

