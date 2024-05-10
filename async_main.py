import asyncio
import json
import time

import csv
import bs4

from fake_useragent import UserAgent
from playwright.async_api import async_playwright, Playwright, expect
from bs4 import BeautifulSoup as Soup


def get_headers() -> str:
    try:
        fake_header: UserAgent = UserAgent().random
    except:
        fake_header: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    return fake_header


saved_data: dict[str, dict] = {'data': {}}
one_site_info = {}


def create_request_urls(uri: str) -> dict:
    domain = uri.split('//')[-1]
    try:
        domain = domain.split('w.')[-1]
    except:
        pass
    creation_modified_request_url: str = f'https://carbondate.cs.odu.edu/cd/{uri}'
    count_tags_url: str = uri
    domain_expire_url: str = f'https://lookup.icann.org/en/lookup'
    trust_trunk_url: str = f'https://www.seomastering.com/audit/{domain}/'
    check_ssl_url: str = uri
    all_urls: dict = {
        'creation_modified_request_url': creation_modified_request_url,
        'count_tags_url': count_tags_url,
        'domain_expire_url': domain,
        'trust_trunk_url': domain,
        'check_ssl_url': check_ssl_url,
    }
    return all_urls


async def get_publish_change_dates(key_url: str, uri: str, playwright: Playwright):
    try:
        chromium = playwright.chromium
        browser = await chromium.launch(headless=True)
        context = await browser.new_context(user_agent=get_headers())
        page = await context.new_page()
        await page.goto(url=uri)
        content = await page.content()
        response_data: dict = json.loads(Soup(content, 'lxml').find('pre').text)
        # response_data: dict = json.loads()
        # response_data: dict = json.loads(content)
        creation_date: str = response_data['estimated-creation-date'].strip().split('T')[0]
        last_modified_date: str = response_data['sources']['last-modified']['earliest'].strip()
        if creation_date:
            creation_date: str = response_data['estimated-creation-date'].strip().split('T')[0]
        else:
            creation_date: str = 'NaN'
        if last_modified_date:
            last_modified_date: str = last_modified_date.split('T')[0]
        else:
            last_modified_date = 'NaN'
        await page.close()
    except Exception:
        creation_date = 'NaN'
        last_modified_date = 'NaN'

    try:
        saved_data['data'][key_url]['creation_date'] = creation_date
        saved_data['data'][key_url]['last_modified_date'] = last_modified_date
    except KeyError:
        saved_data['data'] = {
            key_url:
                {
                    'url': key_url,
                    'creation_date': creation_date,
                    'last_modified_date': last_modified_date,
                }
        }
    await asyncio.sleep(1)


async def count_tags_quantity(key_url: str, uri: str, playwright: Playwright):
    try:
        chromium = playwright.chromium
        browser = await chromium.launch(headless=True)
        context = await browser.new_context(user_agent=get_headers())
        page = await context.new_page()
        await page.goto(url=uri)
        content = await page.content()
        soup: bs4.BeautifulSoup = Soup(content, 'lxml')
        try:
            ol_tags: int = len(soup.find_all('ol'))
        except:
            ol_tags: str = '0'
        try:
            ul_tags: int = len(soup.find_all('ul'))
        except:
            ul_tags: str = '0'
        await page.close()
    except Exception as ex:
        ol_tags: str = '0'
        ul_tags: str = '0'

    try:
        saved_data['data'][key_url]['ol_tags'] = ol_tags
        saved_data['data'][key_url]['ul_tags'] = ul_tags
    except KeyError:
        saved_data['data'] = {
            key_url:
                {
                    'url': key_url,
                    'ol_tags': ol_tags,
                    'ul_tags': ul_tags,
                }
        }
    await asyncio.sleep(1)


async def check_domain_expire_date(key_url: str, domain: str, playwright: Playwright):
    try:
        chromium = playwright.chromium
        browser = await chromium.launch(headless=True)
        context = await browser.new_context(user_agent=get_headers())
        page = await context.new_page()
        await page.goto(url='https://lookup.icann.org/en')
        await page.get_by_placeholder(text='Enter a value').fill(domain)
        await page.keyboard.press('Enter')
        await expect(
            page.locator(
                'xpath=/html/body/rwc-root/div/rwc-lookup-response/div[4]/div[1]/div/div/rwc-lookup-domain-information/div/div/ul[2]/li[1]'
            )
        ).to_be_visible(timeout=30000)
        content = await page.content()
        soup: bs4.Tag = Soup(content, 'lxml').find('ul', class_='item-list')
        date: str = soup.find_all('li')[0].findNext('span', class_='date registry-expiration').text.strip().split(' ')[0]
        await page.close()
    except Exception as ex:
        date = 'NaN'

    try:
        saved_data['data'][key_url]['domain_expire'] = date
    except KeyError:
        saved_data['data'] = {
            key_url:
                {
                    'url': key_url,
                    'domain_expire': date,
                }
        }
    await asyncio.sleep(1)


async def get_trust_rank_value(key_url: str, domain: str, playwright: Playwright):
    try:
        chromium = playwright.chromium
        browser = await chromium.launch(headless=True)
        context = await browser.new_context(user_agent=get_headers())
        page = await context.new_page()
        await page.goto(url='https://www.seomastering.com/', wait_until='domcontentloaded')
        await page.locator('xpath=//*[@id="user"]').fill('User123User')
        time.sleep(1)
        await page.locator('xpath=//*[@id="passwrd"]').fill('1yggNy0jq8rsn4vHsAvL')
        await page.keyboard.press('Enter')
        time.sleep(3)
        await page.goto(url='https://www.seomastering.com/', wait_until='domcontentloaded')
        await page.locator('xpath=//*[@id="content"]/article/div[2]/div[2]/form/input[3]').fill(domain)
        await page.keyboard.press('Enter')
        print('Ожидание получение Trust Trunk value ...')
        await asyncio.sleep(10)
        if page.url == 'https://www.seomastering.com/error.php':
            trust_rank_value = 'NaN'
        else:
            await expect(page.locator('xpath=//*[@id="site_rank"]')).to_be_visible(timeout=60000)
            content = await page.content()
            soup: bs4.BeautifulSoup = Soup(content, 'lxml')
            trust_rank_value: str = [tag.text for tag in soup.find_all('a', class_='tr_col') if
                                     tag['href'] == 'https://www.seomastering.com/trust-rank/'][0]
        await page.close()
    except Exception as ex:
        trust_rank_value = 'NaN'

    try:
        saved_data['data'][key_url]['trust_rank'] = trust_rank_value
    except KeyError:
        saved_data['data'] = {
            key_url:
                {
                    'url': key_url,
                    'trust_rank': trust_rank_value,
                }
        }
    await asyncio.sleep(1)


async def check_ssl(uri: str):
    protocol: str = uri.split('://')[0]
    if protocol[-1] == 's':
        ssl_value: str = 'Yes'
    else:
        ssl_value: str = 'No'
    try:
        saved_data['data'][uri]['ssl'] = ssl_value
    except KeyError:
        saved_data['data'] = {
            uri:
                {
                    'url': uri,
                    'ssl': ssl_value,
                }
        }
    await asyncio.sleep(1)


async def gather_data(line_idx: int):
    with open('competitors_processed.csv', 'r', encoding='utf-8') as read_urls_file:
        reader: list = list(csv.reader(read_urls_file))
        url: str = reader[line_idx][0]
        tasks: list[asyncio.Task] = []
        all_urls: dict = create_request_urls(uri=url)
        async with async_playwright() as playwright:
            tasks.append(asyncio.create_task(get_publish_change_dates(
                key_url=url, uri=all_urls['creation_modified_request_url'], playwright=playwright)))
            tasks.append(asyncio.create_task(count_tags_quantity(
                key_url=url, uri=all_urls['count_tags_url'], playwright=playwright)))
            tasks.append(asyncio.create_task(check_domain_expire_date(
                key_url=url, domain=all_urls['domain_expire_url'], playwright=playwright)))
            tasks.append(asyncio.create_task(get_trust_rank_value(
                key_url=url, domain=all_urls['trust_trunk_url'], playwright=playwright)))
            tasks.append(asyncio.create_task(check_ssl(uri=url)))
            await asyncio.gather(*tasks)


if __name__ == '__main__':
    try:
        with open('competitors_processed_c.csv', 'r', encoding='utf-8') as f:
            reader: csv.reader = csv.reader(f)
    except FileNotFoundError:
        with open('competitors_processed_c.csv', 'a', encoding='utf-8') as file:
            writer: csv.writer = csv.writer(file)
            writer.writerow(
                [
                    'url',
                    'trust_rank',
                    'domain_expire',
                    'ul_tags',
                    'ol_tags',
                    'creation_date',
                    'last_modified_date',
                    'ssl',
                ]
            )
    idx: int = 0
    with open('competitors_processed.csv', 'r', encoding='utf-8') as urls_file:
        r: list = list(csv.reader(urls_file))
    while idx <= len(r):
        asyncio.run(gather_data(idx))

        idx += 1
        link = list(saved_data['data'].keys())[0]
        with open('competitors_processed_c.csv', 'a', encoding='utf-8') as result_file:
            field_names = list(saved_data['data'][link].keys())
            writer: csv.writer = csv.writer(result_file)
            writer.writerow(
                [
                    saved_data['data'][link]['url'],
                    saved_data['data'][link]['trust_rank'],
                    saved_data['data'][link]['domain_expire'],
                    saved_data['data'][link]['ul_tags'],
                    saved_data['data'][link]['ol_tags'],
                    saved_data['data'][link]['creation_date'],
                    saved_data['data'][link]['last_modified_date'],
                    saved_data['data'][link]['ssl'],
                ]
            )
        print(f"Сохранено для сайта {saved_data['data'][link]['url']}")
        saved_data['data'] = {}
