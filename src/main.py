import logging
import re
from collections import Counter
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (BASE_DIR, DOWNLOADS_DIR, MAIN_DOC_URL,
                       EXPECTED_STATUS, PEP8_DOC_URL)
from exceptions import ParserFindTagException
from outputs import control_output
from utils import find_tag, prepare_soup


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    soup = prepare_soup(session, whats_new_url)
    div_with_ul = find_tag(
        soup,
        'section',
        attrs={'id': 'what-s-new-in-python'}
    ).find('div', class_='toctree-wrapper')
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'})
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = section.find('a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        soup = prepare_soup(session, version_link)
        if not soup:
            continue
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append(
            (version_link, h1.text, dl_text)
        )
    return results


def latest_versions(session):
    soup = prepare_soup(session, MAIN_DOC_URL)
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise ParserFindTagException('Не найден список версий Python.')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for tags in a_tags:
        link = tags['href']
        text_match = re.search(pattern, tags.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = tags.text, ''
        results.append(
            (link, version, status)
        )
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    soup = prepare_soup(session, downloads_url)
    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / DOWNLOADS_DIR
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    archive_response = session.get(archive_url)
    if not archive_response.ok:
        return
    with open(archive_path, 'wb') as file:
        file.write(archive_response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    soup = prepare_soup(session, PEP8_DOC_URL)
    rows = soup.select('table.pep-zero-table tbody tr')
    results = []
    for row in tqdm(rows, desc='Обработка статусов PEP'):
        abbr_tag = row.find('abbr')
        if abbr_tag is None:
            continue
        href_tag = row.find('a', attrs={'class': 'pep reference internal'})
        results.append((abbr_tag.text[1:], href_tag['href']))
    pep_statuses = []
    for abbr_status, href_tag in tqdm(results, desc='Сбор статусов'):
        pep_link = urljoin(PEP8_DOC_URL, href_tag)
        response = session.get(pep_link)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, features='lxml')
        section = soup.find('section', attrs={'id': 'pep-content'})
        dl = section.find('dl', attrs={'class': 'rfc2822 field-list simple'})
        status_tag = dl.select_one('dt:contains("Status") + dd')
        pep_statuses.append(status_tag.text)
        if status_tag.text not in EXPECTED_STATUS[abbr_status]:
            logging.info(f"""
                         Несовпадающие статусы:
                         {pep_link}
                         Статус в карточке: {status_tag.text}
                         Ожидаемые статусы: {EXPECTED_STATUS[abbr_status]}
                         """)
    output_results = [('Status', 'Count')]
    pep_counts = Counter(pep_statuses)
    pep_list = list(pep_counts.items())
    output_results.extend(pep_list)
    output_results.append(('Total', len(pep_statuses)))
    return output_results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')
    try:
        arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
        args = arg_parser.parse_args()
        logging.info(f'Аргументы командной строки: {args}')
        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()
        parser_mode = args.mode
        results = MODE_TO_FUNCTION[parser_mode](session)
        if results is not None:
            control_output(results, args)
        logging.info('Парсер завершил работу.')
    except Exception as error:
        logging.critical(
            f'Сбой в работе парсера: {error}',
            exc_info=True
        )
        raise SystemExit(1)


if __name__ == '__main__':
    main()
