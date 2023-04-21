from bs4 import BeautifulSoup
import json
import argparse
from helpers import *
import re
import os
import datetime

parser = argparse.ArgumentParser(description='Check for ticket availability for a given event.')
parser.add_argument('eventid', type=int, help='Event ID')
parser.add_argument('-r', '--recipients', required=True, nargs='+', help='Recipient e-mail addresses')
parser.add_argument('-s', '--sleep', action='store_true', help='Sleep between 5 and 10 minutes before requests')
parser.add_argument('--test', action='store_true', help='Test mode', default=False)
parser.add_argument('-l', '--log', help='Log file used for determining send history', default='log.json')

args = parser.parse_args()

args.eventid = str(args.eventid)


url = event_url(args.eventid)

# read in config file if it exists
log = {}

if os.path.isfile(args.log):
    with open(args.log) as f:
        log = json.load(f)
else:
    print('Warning: Could not find log file')



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
            alert_message += '\nTicket available for ' + product['title'] + ' at ' + event_url(args.eventid)

if 'ticketResaleAvailability' in json_data and json_data['ticketResaleAvailability'] is not None:
    alert_message += '\nTicket resale available at ' + resale_url(args.eventid)

# try to get event title
try:
    event_title = bs.find("meta", property="og:title")['content']
except:
    event_title = args.eventid

# determine whether or not to include recipients in the email
if 'recipients' in log:
    for recipient in args.recipients:
        if recipient not in log['recipients'].keys():

            log['recipients'][recipient] = {}

            log['recipients'][recipient][args.eventid] = {
                'last_state': None,
                'last_alert': None
            }
        elif args.eventid not in log['recipients'][recipient].keys():
            log['recipients'][recipient][args.eventid] = {
                'last_state': None,
                'last_alert': None
            }
else:
    log['recipients'] = {}
    for recipient in args.recipients:

        log['recipients'][recipient] = {}

        log['recipients'][recipient][args.eventid] = {
            'last_state': None,
            'last_alert': None
        }

# only include recipients that had a soldout for the last check or have not been alerted in the last 24 hours
recipients = []

for recipient in args.recipients:
    if log['recipients'][recipient][args.eventid]['last_state'] != 'available' or (log['recipients'][recipient][args.eventid]['last_state'] == 'available' and log['recipients'][recipient][args.eventid]['last_alert'] is not None and (datetime.datetime.now() - datetime.datetime.strptime(log['recipients'][recipient][args.eventid]['last_alert'], '%Y-%m-%d %H:%M:%S')).total_seconds() > 86400) or args.test:
        recipients.append(recipient)


if alert_message != '' or args.test:

    if args.test:
        alert_message = 'THIS IS ONLY A TEST MAIL! \n ' + alert_message

    print('sending email...')
    # send e-mail to recipients

    now = datetime.datetime.now()

    try:
        send_mail("TIXFORGIGS event " + str(event_title) + ' news', alert_message, recipients, sender='mh.max.haag@googlemail.com')
    except Exception as e:
        print('Error: Could not send e-mail')
        print(str(e))
        exit()

    # update log
    if not args.test:

        print('updating log...')

        for recipient in log['recipients'].keys():
            log['recipients'][recipient][args.eventid]['last_state'] = 'available'
            log['recipients'][recipient][args.eventid]['last_alert'] = now.strftime('%Y-%m-%d %H:%M:%S')

        with open(args.log, 'w') as f:
            json.dump(log, f)

else:
    print('no tickets available')

    # update log
    for recipient in log['recipients'].keys():
        log['recipients'][recipient][args.eventid]['last_state'] = 'soldout'

    if not args.test:
        print('updating log...')
        with open(args.log, 'w') as f:
            json.dump(log, f)


    print('done')
