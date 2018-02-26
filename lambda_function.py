import json
import boto3

def lambda_handler(event, context):
        msg = ''
        # Show the incoming event in the debug log
        client = boto3.client('iot-data', region_name='us-west-2')
        if event['food']!="N.A." or event['sides']!="N.A.":
                msg = 1
                send_msg = {
                        'timestamp': event['timestamp'],
                        'orderid': event['orderid'],
                        'food': event['food'],
                        'foodquantity': event['foodquantity'],
                        'sides': event['sides'],
                        'sidesquantity': event['sidesquantity']
                }
                response = client.publish(
                        topic="order/food",
                        qos=1,
                        payload=json.dumps(send_msg)
                )
                if event['drink']==" ":
                        response = client.publish(
                        topic="order/drinkcompleted",
                        qos=1,
                        payload=json.dumps({'orderid': event['orderid']})
                        )

        
        if event['drink']!="N.A.":
                send_msg = {
                        'timestamp': event['timestamp'],
                        'orderid': event['orderid'],
                        'drink': event['drink'],
                        'drinkquantity': event['drinkquantity']
                }
                response = client.publish(
                        topic="order/drink",
                        qos=1,
                        payload=json.dumps(send_msg)
                        )
                if event['food']==" ":
                        response = client.publish(
                        topic="order/foodcompleted",
                        qos=1,
                        payload=json.dumps({'orderid': event['orderid']})
                        )
        return msg
