import boto3
dynamodb = boto3.resource('dynamodb')
food = dynamodb.Table('food')
sides = dynamodb.Table('sides')
drinks = dynamodb.Table('drinks')

with food.batch_writer() as batch:
    batch.put_item(
        Item={'id':'1','name':'McChicken','description':'An evergreen favourite, McChicken has been winning fans with its wholesome great taste - tender chicken patties plus just the right touch of mayo. Just classic.','imagelocation':'/static/chicken.png','price':'2'}
    )
    batch.put_item(
        Item={'id':'2','name':'BBQ Beef Burger with Egg','description':'An evergreen favourite, BBQ Beef Burger with Egg has been winning fans with its wholesome great taste - tender beef patties plus just the right touch of mayo. Just classic.','imagelocation':'/static/beef.png','price':'4'}
    )
    batch.put_item(
        Item={'id':'3','name':'Filet-O-Fish','description':'The catch of the day is sure a great catch at McDonald\'s. A fish filet, smothered with tangy tartar sauce and half a slice of cheese between tender steamed buns is simply pure ocean heaven.','imagelocation':'/static/fish.png','price':'3'}
    )
    batch.put_item(
        Item={'id':'4','name':'Veggie Crunch Burger','description':'An evergreen favourite, Veggie Crunch Burger has been very popular with our fans.','imagelocation':'/static/veggie.png','price':'2.5'}
    )

with sides.batch_writer() as batch:
    batch.put_item(
        Item={'id':'1','name':'Apple Slices','description':'Go fruity with fresh, ready-to-eat apple slices! Delicious also is the fact that every pack of Apple Dippers contains 56mg of vitamin C.','imagelocation':'/static/apple.png','price':'1'}
    )
    batch.put_item(
        Item={'id':'2','name':'Corn Cup','description':'Veg up with crunchy corn kernels and enjoy a yummy serving of antioxidants! Served warm with an optional pat of margarine, it\'s comfort food that\'s oh-so-wholesome.','imagelocation':'/static/corn.png','price':'1.5'}
    )
    batch.put_item(
        Item={'id':'3','name':'French Fries','description':'For winning flavour and texture, we only use premium Russet Burbank variety potatoes for that fluffy inside, crispy outside taste of our world-famous fries.','imagelocation':'/static/fries.png','price':'2'}
    )
    batch.put_item(
        Item={'id':'4','name':'Hashbrown','description':'Golden brown and crispy on the outside, soft and moist on the inside. Who can resist our hearty Hashbrowns?','imagelocation':'/static/hashbrown.png','price':'1'}
    )

with drinks.batch_writer() as batch:
    batch.put_item(
        Item={'id':'1','name':'Coca-Cola','description':'A colde and refreshing complement to all our menu items.','imagelocation':'/static/coke.png','price':'2'}
    )
    batch.put_item(
        Item={'id':'2','name':'Jasmine Green Tea','description':'A soothing fusion of fragrant Jasmine and Green Tea calms your senses.','imagelocation':'/static/greentea.png','price':'3'}
    )
    batch.put_item(
        Item={'id':'3','name':'Hot Tea','description':'Order your regular, or find a new favourite from our selection of international teas of both traditional and herbal varieties.','imagelocation':'/static/hottea.png','price':'1.5'}
    )
    batch.put_item(
        Item={'id':'4','name':'Iced Milo','description':'Cool yourself down instantly with your favourite chocolate drinks swirled with ice.','imagelocation':'/static/milo.png','price':'3'}
    )

