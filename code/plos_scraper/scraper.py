#coding: utf-8
import os
import sys
import time

import re
import urllib
import urllib2

import lxml.html

from collections import deque

STRIP_NEWLINES = (lambda x: re.sub('\n', ' ', x.strip()))
STRIP_HTML_TAGS = (lambda x: re.sub(r'<.*?>', '', x.strip()))
SEARCH = (lambda x,y: re.search(x, y).group(1).strip())

def write_status(status_msg):
   sys.stdout.write('\r%s' % status_msg)
   sys.stdout.flush()

def throttle_sleep(sleep_time):
   write_status("going to sleep for a bit...")
   time.sleep(sleep_time)
   write_status("time to get back to work!")

class plos_connection(object):
   def __init__(self):
      self.base_url = ('http://www.ploscompbiol.org')
      self.seed_url = ('/article/browse.action?field=on&pageSize=10&' +
                       'startPage=85&selectedSubjects=Computer+and+information+sciences')

   '''
      Send HTTP GET to the url 'page_url'. Returns the response to the HTTP
      GET.
   '''
   def get_page(self, page_url, sleep_time=2):
      throttle_sleep(sleep_time)

      attempts = 0
      while (attempts < 5):
         try:
            page_content = urllib2.urlopen(page_url).read()
            return page_content
         except Exception as err:
            attempts += 1

            err_file = open('error.log', 'a')
            err_file.write(('Error. Could not retrieve url "%s".\n%s\n') %
                           (page_url, err))
            err_file.close()

      return None

   '''
      Send HTTP POST to url 'page_url' the values given in the *dictionary*
      'post_params'. Returns the response to the HTTP POST.
   '''
   def post_page(self, page_url, post_params):
      page_response = None

      if (type(post_params) is dict):
         encoded_params = urllib.urlencode(post_params)
         page_response = urllib2.urlopen(page_url, encoded_params).read()

      return page_response

class plos_html_scraper(object):
   def __init__(self, html_content):
      self.html_doc = lxml.html.fromstring(html_content)

   def extract_search_pages(self):
      article_pages = []
      for element in self.html_doc.cssselect('.resultsTab > a'):
         article_pages.append(element.attrib['href'])

      return article_pages

   def extract_article_results(self):
      articles = []

      for result in self.html_doc.cssselect('#searchResults > li'):
         authors = result.cssselect('.authors')[0].text_content().strip('\n ')
         title   = result.cssselect('a')[0].text_content()
         url     = result.cssselect('a')[0].attrib['href']

         articles.append({'url'     : url,
                          'title'   : title,
                          'authors' : authors})

      return articles

   def extract_abstract(self):
      return [para.text_content() for para in self.html_doc.cssselect('.abstract p')]

   def extract_text(self):
      sections = self.html_doc.cssselect('div[id^="section"]')

      article_text = []
      for section in sections:
         for child in section.getchildren():
            if (child.tag == 'h3'):
               tmp_str = re.sub(r'Top', '', child.text_content()).strip()
               article_text.append(tmp_str)

            elif (child.tag == 'h4' or child.tag == 'p'):
               article_text.append(child.text_content())

      return article_text

   def extract_references(self):
      references = self.html_doc.cssselect('.references li')

      ref_list = []
      for reference in references:
         ref_list.append(re.sub(r'\s+', ' ',
                                re.sub(r'\n|Find this article online', '',
                                       reference.text_content())))

      return ref_list

   def extract_reference_links(self):
      references = self.html_doc.cssselect('.references li')

      ref_list = []
      for reference in references:
         link_list = reference.cssselect('.find')

         if (len(link_list) > 0):
            ref_list.append(link_list[0].attrib['href'])
         else:
            ref_list.append(None)

      return ref_list

   def get_pubmed_link(self):
      links = self.html_doc.cssselect('#content li > a')
      for link in links:
         if (re.search(r'ncbi', link.attrib['href'])):
            return link.attrib['href']

      return None

class pubmed_html_scraper(object):
   def __init__(self, html_content):
      self.html_doc = lxml.html.fromstring(html_content)

   def get_meta(self):
      article = self.html_doc.cssselect('.rprt')

      if (len(article) == 1):
         title = self.get_title(article[0])
         authors = self.get_authors(article[0])
         abstract = self.extract_abstract()

         return {'title'    : title,
                 'authors'  : authors,
                 'abstract' : abstract}

      return None

   def get_title(self, html_content):
      return html_content.cssselect('h1')[0].text_content()

   def get_authors(self, html_content):
      return ', '.join([ele.text_content() for ele in
                        html_content.cssselect('.auths a')])

   def extract_abstract(self):
      abstracts = self.html_doc.cssselect('.abstr > p')
      if (len(abstracts) == 1):
         return abstracts[0].text_content()

def debug_scrape_plos(plos_page):
   if (plos_page is not None):
      doc_scraper = plos_html_scraper(plos_page)
      return (doc_scraper.extract_search_pages(),
              doc_scraper.extract_article_results())

   return (None, None)

def scrape_plos_page(plos_conn, plos_search_url):
   plos_page = plos_conn.get_page(plos_conn.base_url + plos_search_url)

   if (plos_page is not None):
      html_scraper = plos_html_scraper(plos_page)

      return (html_scraper.extract_search_pages(),
              html_scraper.extract_article_results())

   return (None, None)

def generate_meta(article_data, doc_parser):
   meta_output = u''

   meta_output += 'TITLE: %s\n' % article_data['title']
   meta_output += 'AUTHORS: %s\n' % article_data['authors']
   meta_output += 'TERMS:\n'
   meta_output += 'CATEGORIES:\n'
   meta_output += 'ABSTRACT:\n'

   for paragraph in doc_parser.extract_abstract():
      meta_output += '%s\n' % paragraph

   return meta_output

def generate_text(article_data, doc_parser):
   text_output = u''

   text_output += '%s\n' % article_data['title']
   text_output += '%s\n' % article_data['authors']
   text_output += 'ABSTRACT\n'

   for paragraph in doc_parser.extract_abstract():
      text_output += '%s\n' % paragraph

   for paragraph in doc_parser.extract_text():
      text_output += '%s\n' % paragraph

   text_output += 'REFERENCES\n'
   ref_ndx = 0
   for reference in doc_parser.extract_references():
      ref_ndx += 1
      text_output += '[%s]\t%s\n' % (ref_ndx, reference)

   return text_output

def generate_references(doc_parser):
   (ref_text, ref_ndx) = ('REFERENCES\n', 0)

   for reference in doc_parser.extract_references():
      ref_ndx += 1
      ref_text += '[%s]\t%s\n' % (ref_ndx, reference)

   return ref_text

def generate_ref_meta(ref_dict):
   meta_output = u''

   if ('title' in ref_dict):
      meta_output += 'TITLE: %s\n' % ref_dict['title']

   if ('authors' in ref_dict):
      meta_output += 'AUTHORS: %s\n' % ref_dict['authors']

   meta_output += 'TERMS:\n'
   meta_output += 'CATEGORIES:\n'

   if ('abstract' in ref_dict):
      meta_output += 'ABSTRACT:\n%s'% ref_dict['abstract']

   return meta_output

def generate_ref_text(ref_dict):
   text_output = u''

   if ('title' in ref_dict):
      text_output += '%s\n' % ref_dict['title']

   if ('authors' in ref_dict):
      text_output += '%s\n' % ref_dict['authors']

   if ('abstract' in ref_dict):
      text_output += 'Abstract:\n%s'% ref_dict['abstract']

   return text_output

def fetch_plos_references(plos_conn, ref_dir, doc_parser, ref_ndx=0):
   for reference_link in doc_parser.extract_reference_links():
      ref_ndx += 1
      if (reference_link is None): continue

      # get the search page for the reference
      ref_search_page = plos_conn.get_page(plos_conn.base_url + reference_link)
      if (ref_search_page is None): continue

      # parse the search page for the pubmed link
      ref_page_parser = plos_html_scraper(ref_search_page)
      pubmed_page = ref_page_parser.get_pubmed_link()

      # grab the pubmed page for the reference and parse it for the abstract and
      # other meta information
      pubmed_html = plos_conn.get_page(pubmed_page)
      if (pubmed_html is None): continue

      sub_ref_dir = os.path.join(ref_dir, '%s' % ref_ndx)
      if (not os.path.exists(sub_ref_dir)):
         os.makedirs(sub_ref_dir)

      # each pubmed doc meta dictionary consists of 3 keys:
      # title, authors, abstract
      pubmed_meta = pubmed_html_scraper(pubmed_html).get_meta()
      if (pubmed_meta is None): continue

      if ('DEBUG' in os.environ):
         err_file = open('error.log', 'a')
         err_file.write(('Currently parsing reference "%s"\n') %
                         pubmed_meta['title'].encode('utf-8'))
         err_file.close()

      # create and populate meta data for the reference
      ref_meta_file = open(os.path.join(sub_ref_dir, 'meta.txt'), 'w+')
      ref_meta_file.write(generate_ref_meta(pubmed_meta).encode('utf-8'))
      ref_meta_file.close()

      # create and populate text for the reference
      text_file = open(os.path.join(sub_ref_dir, 'paper.txt'), 'w+')
      text_file.write(generate_ref_text(pubmed_meta).encode('utf-8'))
      text_file.close()

   return

def write_article_files(article_dir, article, doc_parser):
      # create and populate meta data for the paper
      meta_file = open(os.path.join(article_dir, 'meta.txt'), 'w+')
      meta_file.write(generate_meta(article, doc_parser).encode('utf-8'))
      meta_file.close()

      # create and populate text for the paper
      text_file = open(os.path.join(article_dir, 'paper.txt'), 'w+')
      text_file.write(generate_text(article, doc_parser).encode('utf-8'))
      text_file.close()

      # a file containing just the references
      ref_file = open(os.path.join(article_dir, 'refs.txt'), 'w+')
      ref_file.write(generate_references(doc_parser).encode('utf-8'))
      ref_file.close()

def get_search_page_ndx(plos_search_url):
   return SEARCH(r'startPage=(\d+)', plos_search_url)

def renew_content(root_dir='./data'):
   for article in os.listdir(root_dir):
      article_file = open(os.path.join(root_dir, article, 'paper.html'))
      html_content = article_file.read()
      article_file.close()

      parser = plos_html_scraper(html_content)

      article_dir = os.path.join(root_dir, article)
      write_article_files(article_dir, article, parser)

      ref_dir = os.path.join(article_dir, 'references')
      fetch_plos_references(plos_conn, ref_dir, parser)

def fetch_online_content(root_dir='./data'):
   (visited, articles) = (None, None)

   if (not os.path.exists(root_dir)):
      os.makedirs(root_dir)

   visited_pages = dict()
   (plos_conn, page_queue) = (plos_connection(), deque())

   page_queue.append(plos_conn.seed_url)
   visited_pages[get_search_page_ndx(plos_conn.seed_url)] = True

   while (len(page_queue) > 0):
      search_page_url = page_queue.popleft()
      (new_search_pages, articles) = scrape_plos_page(plos_conn, search_page_url)

      # record the search page number (i.e. 5 if startPage=5 is in the URL) to
      # avoid re-scraping the same search pages
      for new_search_page_url in new_search_pages:
         search_page_ndx = get_search_page_ndx(new_search_page_url)

         if (search_page_ndx not in visited_pages):
            page_queue.append(new_search_page_url)
            visited_pages[search_page_ndx] = True

            # log the search page that has been visited
            if ('DEBUG' in os.environ):
               err_file = open('error.log', 'a')
               err_file.write(('visited page [%s]\n') % search_page_ndx)
               err_file.close()

      # log what article is currently being parsed and scraped
      if ('DEBUG' in os.environ):
         err_file = open('error.log', 'a')
         err_file.write(('Currently parsing search page "%s"\n') % search_page_url)
         err_file.write(('[%s] search pages left in the queue,' +
                         '[%s] search pages visited\n') % (len(page_queue), len(visited_pages)))
         err_file.close()

      if (articles is not None):
         for article in articles:
            html_content = plos_conn.get_page(plos_conn.base_url + article['url'])
            if (html_content is None): continue

            article_dir = os.path.join(root_dir, article['title'])
            # make directory to hold information for the current paper/article
            if (not os.path.exists(article_dir)):
               os.makedirs(article_dir)

            # record what pages are successfully pulled from the interwebs
            if ('DEBUG' in os.environ):
               err_file = open('error.log', 'a')
               err_file.write(('Currently parsing article page "%s"\n') % article['url'])
               err_file.close()

            parser = plos_html_scraper(html_content)
            write_article_files(article_dir, article, parser)

            # a file containing the html of each article page so that it's
            # easier to renew local pages, this only has to be done for online
            # pages
            html_file = open(os.path.join(article_dir, 'paper.html'), 'w+')
            html_file.write(html_content)
            html_file.close()

            # make directories to hold information for each reference of current
            # paper/article
            ref_dir = os.path.join(root_dir, article['title'], 'references')
            if (not os.path.exists(ref_dir)):
               fetch_plos_references(plos_conn, ref_dir, parser)

if (__name__ == '__main__'):
   if ('RENEW_LOCAL' in os.environ):
      renew_content()

   else:
      fetch_online_content()
