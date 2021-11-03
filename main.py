from login import login
from bs4 import BeautifulSoup
from time import sleep
from config import INTERVAL
from send_mail import send_mail
import logging


def get_reports():
    session = login('https://yjs.ustc.edu.cn/default.asp')
    response = session.get('https://yjs.ustc.edu.cn/bgzy/m_bgxk_up.asp')
    soup = BeautifulSoup(response.text, 'lxml')
    key2index = {
        'id': 1,
        'name_zh': 2,
        'name_en': 3,
        'reporter': 4,
        'affiliation': 5,
        'location': 6,
        'date': 7,
        'capacity': 9
    }
    reports = [{
        k: report.select('td')[v].text.strip()
        for k, v in key2index.items()
    } for report in soup.select('#table_info > tbody > tr.bt06')]
    return reports


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler('log.txt'),
                  logging.StreamHandler()])
    print = logging.info

    all_reports = get_reports()
    print(f'Get initial {len(all_reports)} reports: {all_reports}')
    while True:
        sleep(INTERVAL)
        try:
            new_reports = get_reports()
        except Exception as e:
            print(f'Error: {e}, continue ...')
            continue

        found = False
        for report in new_reports:
            if report['id'] not in [x['id'] for x in all_reports]:
                print(f'Found new report: {report}')
                found = True
                send_mail(f"Found new report: {report['name_zh']}",
                          f'Found new report: {report}')
                all_reports.append(report)
        if not found:
            print('No new report(s) found, continue ...')
