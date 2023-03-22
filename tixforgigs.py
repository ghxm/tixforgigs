from bs4 import BeautifulSoup
import json
import argparse
from helpers import *
import re

parser = argparse.ArgumentParser(description='Check for ticket availability for a given event.')
parser.add_argument('eventid', type=int, help='Event ID')
parser.add_argument('-r', '--recipients', required=True, nargs='+', help='Recipient e-mail addresses')
parser.add_argument('-s', '--sleep', action='store_true', help='Sleep between 5 and 10 minutes before requests')
parser.add_argument('--test', action='store_true', help='Test mode', default=False)

args = parser.parse_args()

url = 'https://www.tixforgigs.com/de-de/Event/' + str(args.eventid)

#print(url)

print('sleeping for a while...')
if args.sleep:
    random_sleep(5,10)

alert_message = ''

try:
    response = url_open(url, headers=random_header())
except Exception as e:
    print('Error: Could not open URL')
    print(str(e))
    # @TODO send mail to me
    exit()

bs = BeautifulSoup(response.read(), 'html.parser')

scripts = bs.find_all('script', {'type': 'text/javascript'})

event_script = None

for script in scripts:
    if 'vm.setEventId' in script.text:
        event_script = script
        break

if event_script is None:
    print('Error: Could not find event script')
    exit()

event_script = event_script.text

event_script_lines = [line.strip() for line in event_script.splitlines() if line.strip() != '']

event_script_line = None

for line in  event_script_lines:
    if 'vm.setEventId' in line:
        event_script_line = line
        break

if event_script_line is None:
    print('Error: Could not find event script line')
    exit()

ticket_json = re.split('.+?(?={)', string=event_script_line, maxsplit=1)[1]
ticket_json = re.sub('(?<=\})[;)]+$', '', ticket_json)

json_data = json.loads(ticket_json)

products = json_data['products']

for product in products:
    product_item_types = product['productItemTypes']

    product_is_ticket = False

    for product_item_type in product_item_types:
        if product_item_type['itemTypeId'] == 1:
            product_is_ticket = True
            break

    if product_is_ticket:
        if not product['soldOut']:
            alert_message += '\nTicket available for ' + product['title'] + ' at ' + url

if 'ticketResaleAvailability' in json_data and json_data['ticketResaleAvailability'] is not None:
    alert_message += '\nTicket resale available at ' + url

if alert_message != '' or args.test:
    if args.test:
        alert_message = 'THIS IS ONLY A TEST MAIL! \n ' + alert_message

    print('sending email...')
    # send e-mail to recipients

    try:
        send_mail("TIXFORGIGS event " + str(args.eventid) + ' news', alert_message, args.recipients, sender='mh.max.haag@googlemail.com')
    except Exception as e:
        print('Error: Could not send e-mail')
        print(str(e))


    print('done')
