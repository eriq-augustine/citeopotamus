#coding: utf-8
import os
import sys
import time

import re
import urllib
import urllib2

import lxml.html

STRIP_NEWLINES = (lambda x: re.sub('\n', ' ', x.strip()))
STRIP_HTML_TAGS = (lambda x: re.sub(r'<.*?>', '', x.strip()))
SEARCH = (lambda x,y: re.search(x, y).group(1).strip())

def write_status(status_msg):
   sys.stdout.write('\r%s' % status_msg)
   sys.stdout.flush()

def throttle_sleep():
   write_status("going to sleep for a bit...")
   time.sleep(3)
   write_status("time to get back to work!")

class plos_connection(object):
   def __init__(self):
      self.base_url = ('http://www.ploscompbiol.org')
      self.seed_url = ('/article/browse.action?field=on&pageSize=10&' +
                       'startPage=2&selectedSubjects=Computational+Biology')

   '''
      Send HTTP GET to the url 'page_url'. Returns the response to the HTTP
      GET.
   '''
   def get_page(self, page_url):
      throttle_sleep()

      attempts = 0
      while (attempts < 5):
         try:
            page_content = urllib2.urlopen(page_url).read()
            return page_content
         except Exception as err:
            attempts += 1
            sys.stderr.write('%s' % err)
            sys.stderr.flush()

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

   def extract_reference_links(self):
      references = self.html_doc.cssselect('.references li')

      ref_list = []
      for reference in references:
         link_list = reference.cssselect('.find')
         if (len(link_list) > 0):
            ref_list.append(link_list[0].attrib['href'])

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

def scrape_plos_page(plos_conn, plos_url):
   plos_page = plos_conn.get_page(plos_conn.base_url + plos_url)

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

   return text_output

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

def fetch_plos_references(plos_conn, doc_parser):
   ref_meta_list = []

   for reference_link in doc_parser.extract_reference_links():
      ref_search_page = plos_conn.get_page(plos_conn.base_url + reference_link)

      ref_page_parser = plos_html_scraper(ref_search_page)
      pubmed_page = ref_page_parser.get_pubmed_link()

      pubmed_html = plos_conn.get_page(pubmed_page)
      pubmed_doc = pubmed_html_scraper(pubmed_html)

      # append a dictionary to the list.
      # each pubmed doc meta dictionary consists of 3 keys:
      # title, authors, abstract
      ref_meta_list.append(pubmed_doc.get_meta())

   return ref_meta_list

if (__name__ == '__main__'):
   root_dir = './data'
   (visited, articles) = (None, None)

   if ('DEBUG' in os.environ):
      test_page_file = open('plos_test.html', 'r')
      test_page = test_page_file.read()
      test_page_file.close()

      (test_queue, test_articles) = debug_scrape_plos(test_page)

      test_article_file = open('plos_article_test.html', 'r')
      test_data = test_article_file.read()
      test_article_file.close()

      test_article = plos_html_scraper(test_data)

      print generate_text(test_articles[0], test_article).encode('utf-8')

   else:
      if (not os.path.exists(root_dir)):
         os.makedirs(root_dir)

      plos_conn = plos_connection()
      (page_queue, articles) = scrape_plos_page(plos_conn, plos_conn.seed_url)

      for article in articles:
         html_content = plos_conn.get_page(plos_conn.base_url + article['url'])
         parser = plos_html_scraper(html_content)

         # make directory to hold information for the current paper/article
         article_dir = os.path.join(root_dir, article['title'])
         if (not os.path.exists(article_dir)):
            os.makedirs(article_dir)

         # create and populate meta data for the paper
         meta_file = open(os.path.join(article_dir, 'meta.txt'), 'w+')
         meta_file.write(generate_meta(article, parser).encode('utf-8'))
         meta_file.close()

         # create and populate text for the paper
         text_file = open(os.path.join(article_dir, 'paper.txt'), 'w+')
         text_file.write(generate_text(article, parser).encode('utf-8'))
         text_file.close()

         # make directories to hold information for each reference of current
         # paper/article
         ref_ndx = 0
         for ref_meta in fetch_plos_references(plos_conn, parser):
            ref_ndx += 1

            if (ref_meta is None): continue

            ref_dir = os.path.join(root_dir, article['title'],
                                   'references', '%s' % ref_ndx)

            if (not os.path.exists(ref_dir)):
               os.makedirs(ref_dir)

               # create and populate meta data for the reference
               ref_meta_file = open(os.path.join(ref_dir, 'meta.txt'), 'w+')
               ref_meta_file.write(generate_ref_meta(ref_meta).encode('utf-8'))
               ref_meta_file.close()

               # create and populate text for the reference
               text_file = open(os.path.join(ref_dir, 'paper.txt'), 'w+')
               text_file.write(generate_ref_text(ref_meta).encode('utf-8'))
               text_file.close()
