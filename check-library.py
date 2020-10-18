#!/usr/bin/env python3

'''
Automatically check library website for new DVD titles
Send email notification when new titles found
'''

import requests
from bs4 import BeautifulSoup
import datetime
import time
import itertools
import smtplib

def send_email(text, gmail_user, gmail_pwd, email_list):
    '''
    Send email notification of new titles
    '''
    FROM = gmail_user
    TO = email_list
    SUBJECT = "New DVDs on order"

    # Prepare actual message
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, text)
    try:
        #server = smtplib.SMTP(SERVER) 
        server = smtplib.SMTP("smtp.gmail.com", 587) #or port 465 doesn't seem to work!
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        #server.quit()
        server.close()
        print 'successfully sent the mail'
    except:
        print "failed to send mail"

def crawl_page(url, user_agent):
    '''
    url: url for a single page
    get all DVD titles from that page
    Return: list of titles
    '''
    try:
        page_response = requests.get(url, headers=user_agent, timeout=5)
    except Exception as e:
        print('exception: ',e)
        return 'error'
    soup = BeautifulSoup(page_response.content, "xml")

    titles = [title.text for title in soup.find_all('title')[1:]]
    # skip the first entry which is "bl results for oo:(true)"
    
    return titles

def crawl_all(url, user_agent, n_repeat, delay):
    '''
    url: contains {} so use string formatting to add in page number there
    n_repeat: how many times to repeat for each page number
    (since sometimes it gives different results if you try it a few times)
    delay: time in seconds between crawling each page
    return: set of found titles
    '''
    found_titles = set()
    for page_number in range(1,100):
        print(page_number)
        for _ in range(n_repeat):
            titles = crawl_page(url.format(page_number), user_agent)
            if titles == 'error':
                continue
            elif not titles:
                return found_titles
            found_titles.update(titles)
            print(len(found_titles)),
            time.sleep(delay)
    return found_titles

def read_file(dvd_file):
    '''
    reads in all found dvds from file
    removes any comments
    returns as a set
    '''
    with open(dvd_file) as f:
        all_titles = f.readlines()
    all_titles = [title.strip() for title in all_titles if not title.startswith('#')]
    all_titles = set(all_titles)
    return all_titles

def append_new_titles(dvd_file, new_titles, today):
    '''
    dvd_file: file containing all found titles
    new_titles: set of new_titles to append
    today: datetime of today to add as comment
    '''
    with open(dvd_file,'a') as f:
        f.write('#{}\n'.format(today))
        for title in new_titles:
            f.write('{}\n'.format(title))

def calculate_wait(hours_to_check):
    '''
    TO DO:
    hours_to_check: list of hours (from 0-24) for which to check site
    returns: how many seconds to wait until next check
    '''
    pass

def wrapper(url, user_agent, n_repeat, delay, 
	gmail_user, gmail_pwd, email_list, dvd_file):
    '''
    Main loop of program
    Crawls through all the library pages to find new titles
    Appends new titles to dvd_file
    Sends email notifying of new titles
    Then waits for next time to search
    '''
    while True:
        today = datetime.datetime.today()
        print(today)
        titles = crawl_all(url, user_agent, n_repeat, delay)

        old_titles = read_file(dvd_file)
        new_titles = titles - old_titles

        if new_titles:
            text_string = '{} new titles were found\n'.format(len(new_titles))
            print(text_string)
            for title in new_titles:
                text_string += '{}\n'.format(title)
            send_email(text_string, gmail_user, gmail_pwd, email_list)
            append_new_titles(dvd_file, new_titles, today)

        wait_time = int(calculate_wait(hours_to_check).seconds)
        print('sleeping for {} seconds...'.format(wait_time))
        time.sleep(wait_time)


gmail_user = "PUT GMAIL ADDRESS HERE"
gmail_pwd = "PUT GMAIL PWD HERE"
email_list = ["EMAIL ADDRESS 1", "EMAIL ADDRESS 2",]
user_agent = {'User-agent':'PUT USER AGENT HERE'}
# url is from searching "On Order" and then selecting just "DVD" and then clicking RSS icon
url = 'https://gateway.bibliocommons.com/v2/libraries/slpl/rss/search?query=oo%3A(true)&searchType=bl&custom_edit=true&f_FORMAT=DVD&pagination_page={}&suppress=true&title=On Order&view=small'
n_repeat = 5
delay = 5
dvd_file = 'dvd_list.txt'
hours_to_check = [0,8,10,12,14,16,18] # hours of day to check

wrapper(url, user_agent, n_repeat, delay, gmail_user, gmail_pwd, email_list, dvd_file)
