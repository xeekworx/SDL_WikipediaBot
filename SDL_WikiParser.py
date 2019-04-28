import re
from collections import OrderedDict 
import requests


class SDL_WikiParser(object):
    def __init__(self, wiki_url):
        self.wiki_url = wiki_url

    def parse(self, content, source_url):
        content = content.decode('utf-8') if isinstance(content, bytes) else str(content)
        # Remove any lines starting with # in the content:
        content = re.sub(r'(?m)^\#.*\n?', '', content)
        content = content.strip()

        # There's a category area at the bottom of the document, dump this
        content = content.split('----')[0]

        # Split the sections from content:
        m = re.split('\r\n=', content, re.MULTILINE)
        m = list(filter(None, m)) # Get rid of empty sections
        if not m or len(m) < 2:
            return None

        result = OrderedDict() # Order is important when the sections are displayed
        is_title = True # The first section will be split into 'Title' and 'Summary'

        for section in m:
            tmp = section.split("=\r\n", 1)
            section_title = tmp[0].replace('=', '').strip()
            section_content = clean_up_text(tmp[1])
            section_content = syntax_highlight(section_content)
            section_content = generate_emojis(section_content)
            section_content = dealwith_tables(section_content)
            section_content = generate_links(section_content, self.wiki_url, source_url)

            if is_title:
                result['Title'] = section_title
                result['Summary'] = section_content.strip('\r\n')
                is_title = False
            else:
                result[section_title] = section_content

        return result

def clean_up_text(text):
    result = text
    #result = result.replace('\r', '').replace('\n', '').strip()
    result = result.strip('\r\n').strip()
    result = result.replace('<<TableOfContents()>>', '')
    return result

def find_between(s, start, end):
    try:
        return (s.split(start))[1].split(end)[0]
    except:
        return None

def syntax_highlight(text):
    result = text
    result = result.replace('{{{#!highlight cpp\r\n', str("""```cpp\n"""))
    result = result.replace('{{{#!highlight cpp', str("""```cpp\n"""))
    result = result.replace('}}}', str("""```"""))
    return result

def generate_emojis(text):
    result = text
    result = result.replace('/!\\', ":warning:")
    return result

def dealwith_tables(text):
    result = text
    result = result.replace("||'''", "**`")
    result = result.replace("'''||", "`** - ")
    result = result.replace('||', '')
    #result = result.replace("'''", '**')
    result = result.strip()
    return result

def generate_links(text, base_url, source_url):
    result = text
    result = result.replace('.[[', '[[')

    for m in re.finditer('''\[\[.*?\]\]''', result, re.MULTILINE):
        new = m.group(0).replace('[[', '').replace(']]', '')
        old = m.group(0)
        pipe_pos = new.find('|')
        if pipe_pos >= 0:
            group_name = new[pipe_pos+1:]
            group_url = source_url + new[0:pipe_pos]
        else:
            group_name = new
            group_url = base_url + new

        new = '[{0}]({1})'.format(group_name, group_url)
        result = result.replace(old, new)

    return result
