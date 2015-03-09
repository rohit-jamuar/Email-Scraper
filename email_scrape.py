#!/usr/bin/python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from selenium import webdriver
from re import compile, IGNORECASE
from urlparse import urlparse


class EmailScraper(object):

    '''
    Email scraper v0.1

    External Dependencies :
    1. Selenium      -- sudo pip install selenium
    2. BeautifulSoup -- sudo pip install BeautifulSoup4
    '''

    def __init__(self, domain_name=None):
        if domain_name and is_valid_domain(domain_name):
            self.domain_name = 'www.{}'.format(domain_name) \
                if not domain_name.startswith('www') else domain_name
        else:
            print 'Invalid domain-name passed!'
            exit(1)
        self.driver = webdriver.Firefox()
        self.visited = {'/'}
        self.extracted_mail = set()

    def extract_mail_add(self):
        '''
        This method is the publicly available method which in-turn is
        responsible for finding all the email-addresses within a domain. The
        extraction follows DFS traversal, once the traversal completes, the
        collected email-addresses are printed in a one-per-line fashion.
        '''
        node_list = ['http://{}/'.format(self.domain_name)]
        while node_list:
            current_node = node_list.pop()
            if current_node not in self.visited:
                self.visited.add(current_node)
                html_response = get_html(current_node, self.driver)
                if html_response:
                    node_list.extend(fetch_links(html_response,
                                                 self.domain_name,
                                                 self.visited))
                    for address in find_mail_address(html_response):
                        self.extracted_mail.add(address)
        self.driver.close()
        if self.extracted_mail:
            print 'Found these email address(es) :'
            for address in self.extracted_mail:
                print address
        else:
            print 'Could not find an email-address on {}!'.\
                format(self.domain_name)


def get_html(link=None, driver=None):
    '''
    This function is responsible for taking the URL (passed via 'link' arg)
    and making the HTTP request. The HTML is stripped from the response
    and returned to caller as a BeautifulSoup object.
    '''
    if link and driver:
        driver.get(link)
        return BeautifulSoup(driver.page_source)


def in_same_domain(source, target):
    '''
    Function checks whether 'target' URL has the same domain-name as the
    'source'.
    '''
    return source.split('.')[-2:] == urlparse(target).netloc.split('.')[-2:]


def find_mail_address(html_corpus=None):
    '''
    This function finds all e-mails in the 'html_corpus'. Admittedly, the
    regex is not as extensive as it could be, but for most cases, the
    current pattern should suffice. Regex was chosen as it would be
    particularly difficult to write a generic XPath query for finding
    email addresses from DOM with varying (perhaps, extremely
    nested) structures. The addresses are returned as a list.
    '''
    return [mail for mail in html_corpus.
            find_all(text=compile(r'\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,6}'))]


def fetch_links(html_corpus=None, domain_name=None, visited_links=None):
    '''
    This function fetches all the URLs (belonging to the domain-name passed
    as command-line arg) from the 'html_corpus'. This method also
    rewrites relative-links to their absolute form - 'get_html'
    method would only work with absolute links.
    '''
    links = []
    if all([html_corpus, domain_name, visited_links,
            isinstance(visited_links, set)]):
        for link in html_corpus.find_all('a'):
            link = link.get('href', None)
            if link:
                if link.startswith('/'):
                    to_traverse = "http://{}{}".format(domain_name, link)
                    if to_traverse not in visited_links:
                        links.append(to_traverse)
                elif in_same_domain(domain_name, link) \
                        and link not in visited_links:
                    links.append(link)
    return links


def is_valid_domain(domain_name=None):
    '''
    This function checks whether the passed argument qualifies as valid
    domain name or not.
    '''
    if type(domain_name) != str or len(domain_name) > 255:
        return False
    if domain_name[-1] == ".":
        domain_name = domain_name[:-1]
    allowed = compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", IGNORECASE)
    return all(allowed.match(x) for x in domain_name.split("."))

if __name__ == '__main__':
    from sys import argv
    if len(argv) == 2:
        ESCRAPER = EmailScraper(argv[1].strip()).extract_mail_add()
    else:
        print 'Improper number of arguments passed!!'
