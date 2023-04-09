
import os
import re
import configparser
import markdown2 as mk2
import pickle
import wi_code.org_info as oi

nav_bar_template = """
<nav class="nav_bar">
<ul id="navlist">
<li class="navitem"><a href="{prev_link}" style="background-color:rgb({flower_color});">previous</a></li>
<li class="navitem"><a href="{toc_link}" style="background-color:rgb({flower_color});">table of contents</a></li>
<li class="navitem"><a href="{next_link}" style="background-color:rgb({flower_color});">next</a></li>
</ul>
</nav>
"""

beg_nav_bar_template = """
<nav class="nav_bar">
<ul id="navlist">
<li class="navitem"><a href="{curr_link}" style="background-color:rgb({flower_color});">beginning</a></li>
<li class="navitem"><a href="{toc_link}" style="background-color:rgb({flower_color});">table of contents</a></li>
<li class="navitem"><a href="{next_link}" style="background-color:rgb({flower_color});">next</a></li>
</ul>
</nav>
"""

end_nav_bar_template = """
<nav class="nav_bar">
<ul id="navlist">
<li class="navitem"><a href="{prev_link}" style="background-color:rgb({flower_color});">previous</a></li>
<li class="navitem"><a href="{toc_link}" style="background-color:rgb({flower_color});">table of contents</a></li>
<li class="navitem"><a href="{curr_link}" style="background-color:rgb({flower_color});">ending</a></li>
</ul>
</nav>
"""

page_template = """
<head>
<link rel="stylesheet" href="./css/main.css"/>
<title>{poem_name}: {flower_name}</title>
</head>

<body class="flower_page">
<div id="{flower_name}" class="wi_{orientation}_page" 
 style="background-image: url({image_url});">
{{nav_bar}}
<div class="flower_box" style="background-color:rgb({flower_color}, .75);">
{box_html}
</div>
<div class="picture_link" style="background-color:rgb({flower_color}, .75);">
<a href={pic_source_link}>
{pic_source_text}
</a>
</div>
</div>
</body>
"""

main_template = """
# {flower_name}

{detail}
"""

detail_template = """
**{title}**: {info}
"""

toc_main = """1. {poem_name}  """
toc_sub = """  - [{flower_name}]({page_loc})  """

outer_html = """
<head>
<link rel="stylesheet" href="./css/main.css"/>
</head>

<body class="{page_type}">
{formatted_markdown}
</body>

"""

inner_gloss_link = """
<a href="./glossary.html#{term}" title="{definition}" class="subtle_link">{disp_term}</a>
"""

post_item_templ = """
1. <a href="{item_path}">{item_name}</a>
"""

toc_template = """
# A botanical companion to The Wild Iris
{summary_statement}

## Table of contents

{pre_items}

### The Wild Iris
{items}

### Appendix
{post_items}
"""

glossary_template = """
# Glossary

{items}

"""

glossary_line = """
**{term} <a name="{term}"></a>** - {definition}
"""


img_pdf_options_vert = {
    'page-height': '8.5in',
    'page-width': '5.5in',
}

img_pdf_options_horiz = {
    'page-height': '8.5in',
    'page-width': '11in',
    'page-orientation': 'Landscape',
}

img_pdf_options = {
    'margin-top': '0in',
    'margin-right': '0in',
    'margin-bottom': '0in',
    'margin-left': '0in',
    'encoding': "UTF-8",
    'custom-header': [
        ('Accept-Encoding', 'gzip')
    ],
    'no-outline': None,
    'enable-local-file-access': None,
}


swap_list = (('-', ' '),
             ('@', "'"))
def format_flower_name(s, make_swaps=swap_list):
    for (old, new) in swap_list:
        s = s.replace(old, new)
    return s.title()

ordered_fields = ('Other names', 'Family', 'Type', 'Blooming period',
                  'Sun requirement', 'Soil requirement',
                  'Notes')
last_fields = ('Sources',)
def format_detail(info, ordered_fields=ordered_fields,
                  detail_template=detail_template, last_fields=last_fields):
    ordered_lower = list(of.lower() for of in ordered_fields + last_fields)
    additional_fields = set(info.keys()).difference(ordered_lower)
    field_order = ordered_fields + tuple(additional_fields) + tuple(last_fields)
    out_str = ''
    for field in field_order:
        txt = info.get(field)
        if txt is not None:
            add_str = detail_template.format(title=field, info=txt)
            out_str = out_str + add_str + '\n'
    return out_str


def read_files(folder, file_template='.*\.info$',
               picture_folder='formatted_pictures/{templ}/',
               use_gloss=oi.glossary):
    """
    this reads all the info files and formats them into a markdown
    string for conversion to html or latex
    """
    files = os.listdir(folder)
    page_dict = {}
    for fl in files:
        m = re.match(file_template, fl)
        if m is not None:
            name_str, _ = fl.split('.')
            flower_name = format_flower_name(name_str)
            parser = read_info(fl, folder)
            detail = format_detail(parser['info'])
            page_txt = main_template.format(flower_name=flower_name,
                                            detail=detail)
            page_html = mk2.markdown(page_txt)
            page_html = link_glossary(page_html, use_gloss)
            
            pic_file = parser['picture'].get('path')
            orientation = parser['picture'].get('orientation')
            if orientation is None:
                orientation = 'horizontal'
            p_source_link = parser['picture'].get('source_url')
            p_source_text = parser['picture'].get('source_text')

            flower_folder = picture_folder.format(templ=name_str)
            flower_pic = os.path.join(flower_folder, pic_file)
            col_file = open(os.path.join(flower_folder, 'color.pkl'), 'rb')
            flower_col = pickle.load(col_file)

            page = page_template.format(flower_name=flower_name,
                                        image_url=flower_pic,
                                        flower_color=flower_col,
                                        box_html=page_html,
                                        orientation=orientation,
                                        pic_source_link=p_source_link,
                                        pic_source_text=p_source_text,
                                        poem_name='{poem_name}')
            page_dict[name_str] = (flower_name, page, flower_col)
    return page_dict

def link_glossary(html, term_dict, repl_templ=inner_gloss_link):
    replacements = []
    for term, definition in term_dict.items():
        pattern = '(semi-)?{term}[,s)]?'.format(term=term)
        term_re = re.compile(pattern, re.I)
        m = re.search(term_re, html)
        if m is not None:
            repl_str = m.group()
            new_str = repl_templ.format(term=term, disp_term=repl_str,
                                        definition=definition)
            goofy = str(hash(repl_str))
            html = html.replace(repl_str, goofy)
            replacements.append((goofy, new_str))
    for (r_s, n_s) in replacements:
        html = html.replace(r_s, n_s)
    return html


""" 
TO DO
----- 
1. Fix sources
2. Write short intro
3. Change out all vertical images

"""
def make_html(folder, use_toc=oi.toc, use_gloss=oi.glossary,
              use_post_toc=oi.post_toc,
              toc_template=toc_template,
              toc_main=toc_main, toc_sub=toc_sub, toc_html_templ=outer_html,
              toc_fname='toc.html', gloss_line_templ=glossary_line,
              gloss_fname='glossary.html',
              gloss_mkd_templ=glossary_template,
              gloss_html_templ=outer_html,
              nav_bar_templ=nav_bar_template,
              end_nav_bar_templ=end_nav_bar_template,
              beg_nav_bar_templ=beg_nav_bar_template,
              summary_statement_file='summary_statement.md',
              **kwargs):
    page_dict = read_files(folder, **kwargs)

    ref_dict = {}
    for fname, (flower_name, page, flower_color) in page_dict.items():
        save_name = fname + '_{pg_num}.html'
        ref_dict[fname] = (flower_name, save_name, page, flower_color)
    toc_lines = []
    write_later = []
    for (poem_name, poem_page), flowers in use_toc.items():
        toc_lines.append(toc_main.format(poem_name=poem_name))
        for flower in flowers:
            flower_name, page_name, page, flower_color = ref_dict[flower]
            page_loc = page_name.format(pg_num=poem_page)
            write_later.append((page_loc, poem_name, flower_name, page,
                                flower_color))
            toc_lines.append(toc_sub.format(flower_name=flower_name,
                                             page_loc=page_loc))
    n_pages = len(write_later)
    for i, page_info  in enumerate(write_later):
        (curr_path, curr_pname, curr_fname, curr_page,
         flower_color) = page_info
        toc_link = 'toc.html'
        if i == 0:
            next_path, next_pname, next_fname, next_page, _ = write_later[i+1]
            nav_bar = beg_nav_bar_templ.format(toc_link=toc_link,
                                               next_link=next_path,
                                               curr_link=curr_path,
                                           flower_color=flower_color)
        elif i == n_pages - 1:
            prev_path, prev_pname, prev_fname, prev_page, _ = write_later[i-1]
            nav_bar = end_nav_bar_templ.format(toc_link=toc_link,
                                               prev_link=prev_path,
                                               curr_link=curr_path,
                                           flower_color=flower_color)
        else:
            prev_path, prev_pname, prev_fname, prev_page, _ = write_later[i-1]
            next_path, next_pname, next_fname, next_page, _ = write_later[i+1]
            nav_bar = nav_bar_templ.format(toc_link=toc_link,
                                           prev_link=prev_path,
                                           next_link=next_path,
                                           flower_color=flower_color)
        curr_page_f = curr_page.format(nav_bar=nav_bar,
                                       poem_name=curr_pname)
        with open(curr_path, 'wt') as f:
            f.write(curr_page_f)

    post_toc_lines = []
    for (section_name, link) in use_post_toc.items():
        item = post_item_templ.format(item_name=section_name,
                                      item_path=link)
        post_toc_lines.append(item)
    post_items = '\n'.join(post_toc_lines)
    print(post_items)
    main_items = '\n'.join(toc_lines)

    summary_statement = open(summary_statement_file, 'r').read()
    toc_html = mk2.markdown(toc_template.format(
        pre_items='',
        items=main_items,
        post_items=post_items,
        summary_statement=summary_statement,
    ))
    toc_full = toc_html_templ.format(page_type='org_page',
                                     formatted_markdown=toc_html)
    with open(toc_fname, 'wt') as f:
        f.write(toc_full)

    gloss_lines = [] 
    for term, definition in use_gloss.items():
        gloss_lines.append(
            gloss_line_templ.format(term=term, definition=definition))
    gloss_mkd = gloss_mkd_templ.format(
        items='\n'.join(gloss_lines))
    gloss_html = mk2.markdown(gloss_mkd)
    gloss_full = gloss_html_templ.format(page_type='org_page',
                                         formatted_markdown=gloss_html)
    with open(gloss_fname, 'wt') as f:
        f.write(gloss_full)

def read_info(fl, folder=''):
    parser = configparser.ConfigParser()
    info = parser.read(os.path.join(folder, fl))
    return parser
