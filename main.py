from threading import Thread
import sqlite3
import random
from handler import Handler

connection = sqlite3.connect("emails.db")
cursor = connection.cursor()

# Define the SELECT query
query = "SELECT provider, api_url, api_key FROM number_provider where status='active'"

# Execute the query
cursor.execute(query)

# Fetch all rows from the result
providers = cursor.fetchall()
if providers:
    # random.shuffle(providers)
    # print(providers)
    random_provider = random.choice(providers)
    print(f'selected provider: {random_provider[0]}')
    obj = Handler('proxy.okeyproxy.com', 31212, proxy_user='customer-jrs3267456-country-CY', proxy_password='de7cakrz', number_provider=random_provider)
    # obj = Handler('1.1.1.1', 1111, number_provider=random_provider)
    obj.run()
else:
    print("No active providers found")