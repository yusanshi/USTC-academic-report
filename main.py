from login import login
from bs4 import BeautifulSoup
from time import sleep
from config import *
import logging
import subprocess
import datetime
import pytz
import json
import requests
import tempfile
import urllib.parse
import os
import time


def get_reports():
    error_count = 0
    while True:
        try:
            session = login('https://yjs.ustc.edu.cn/default.asp')
            reports = []
            for page_id in range(1, REPORTS_PAGE_COUNT + 1):
                response = session.get(
                    f'https://yjs.ustc.edu.cn/bgzy/m_bgxk_up.asp?querytype=kc&page={page_id}'
                )
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
                reports.extend([{
                    k: report.select('td')[v].text.strip()
                    for k, v in key2index.items()
                } for report in soup.select('#table_info > tbody > tr.bt06')])
            return reports

        except Exception:
            print('Retry getting reports')
            error_count += 1
            if error_count >= 3:
                raise
            time.sleep(1)


def generate_calendar_links(report):
    title = f"学术报告-{report['id']}-{report['name_zh']}-{report['reporter']}"
    description = f"location: {report['location']}"
    start = datetime.datetime.strptime(
        report['date'], '%Y年%m月%d日%H时%M分').astimezone(
            pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S %z')
    links = json.loads(
        subprocess.check_output([
            'node', 'calendar2link/main.js', '--title', title, '--description',
            description, '--start', start
        ],
                                text=True))
    prefix = 'data:text/calendar;charset=utf8,'
    assert links['ics'].startswith(prefix)
    links['ics'] = links['ics'][len(prefix):]
    ics_text = urllib.parse.unquote(links['ics'])
    dir_path = tempfile.mkdtemp()
    ics_filename = f"学术报告-{report['id']}.ics"
    ics_path = os.path.join(dir_path, ics_filename)
    with open(ics_path, 'w') as f:
        f.write(ics_text)
    subprocess.check_output(['scp', ics_path, SCP_TARGET])
    links['ics'] = urllib.parse.urljoin(SCP_TARGET_URL, ics_filename)
    return links


def generate_html(report, calendar_links):
    with open('report.html', encoding='utf-8') as f:
        html = f.read()
    for key, value in report.items():
        if key != 'id':
            html = html.replace(f"###{key}###", value)
    for key, value in calendar_links.items():
        shorten_text = (value[:64] + '...') if len(value) > 64 else value
        html = html.replace(f"###{key}_text###", shorten_text)
        html = html.replace(f"###{key}_url###", value)
    return html


def listmonk_report(report):
    calendar_links = generate_calendar_links(report)
    html = generate_html(report, calendar_links)
    session = requests.Session()
    session.auth = (LISTMONK_ADMIN, LISTMONK_PASSWORD)
    settings = json.loads(
        session.get(urllib.parse.urljoin(LISTMONK_URL, '/api/settings')).text)
    lists = json.loads(
        session.get(
            urllib.parse.urljoin(LISTMONK_URL,
                                 '/api/lists?per_page=all')).text)
    lists_name = ['中科大学术报告通知（全部学院）']
    if report['affiliation'] == '011':
        lists_name.append('中科大学术报告通知（计算机学院）')
    templates = json.loads(
        session.get(
            urllib.parse.urljoin(LISTMONK_URL,
                                 '/api/templates?per_page=all')).text)
    templates = [
        x for x in templates['data'] if x['name'] == LISTMONK_TEMPLATE_NAME
    ]
    assert len(templates) == 1
    data = {
        "name":
        f"学术报告-{report['id']}",
        "subject":
        f"新报告：{report['id']}-{report['name_zh']}-{report['reporter']}",
        "lists":
        [x['id'] for x in lists['data']['results'] if x['name'] in lists_name],
        "from_email":
        settings['data']['app.from_email'],
        "content_type":
        "richtext",
        "messenger":
        "email",
        "type":
        "regular",
        "tags": [],
        "template_id":
        templates[0]['id']
    }
    request = session.post(urllib.parse.urljoin(LISTMONK_URL,
                                                '/api/campaigns'),
                           json=data)
    assert request.ok
    response = json.loads(request.text)

    campaign_id = response['data']['id']
    data["send_later"] = False
    data["send_at"] = None
    data["body"] = html
    data["altbody"] = None
    request = session.put(urllib.parse.urljoin(
        LISTMONK_URL, f'/api/campaigns/{campaign_id}'),
                          json=data)
    assert request.ok
    request = session.put(urllib.parse.urljoin(
        LISTMONK_URL, f'/api/campaigns/{campaign_id}/status'),
                          json={"status": "running"})
    assert request.ok


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
                listmonk_report(report)
                all_reports.append(report)
                # Sleep for some time to avoid tricky bug
                # with simultaneous campaigns of listmonk
                sleep(60)
        if not found:
            print('No new report(s) found, continue ...')
