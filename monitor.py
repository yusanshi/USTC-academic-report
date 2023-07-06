from config import *
import requests
import urllib.parse
import json
from time import sleep
import logging


def get_campaigns_status():
    session = requests.Session()
    session.auth = (LISTMONK_ADMIN, LISTMONK_PASSWORD)
    campaigns = json.loads(
        session.get(
            urllib.parse.urljoin(
                LISTMONK_URL,
                '/api/campaigns?per_page=all')).text)['data']['results']
    status = {campaign['id']: campaign['status'] for campaign in campaigns}
    return status


def check():
    status = get_campaigns_status()
    non_finshed = [k for k, v in status.items() if v != 'finished']
    if len(non_finshed) > 0:
        print(f'Found not finished campaigns: {non_finshed}, waiting...')
        sleep(INTERVAL)
        new_status = get_campaigns_status()
        for k in non_finshed:
            assert new_status[k] == 'finished'
    else:
        print('All campaigns finished')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.StreamHandler()])
    print = logging.info

    count = 1
    while True:
        print(f'Checking for {count} times')
        check()
        sleep(INTERVAL)
        count += 1
