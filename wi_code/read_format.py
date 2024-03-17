import os
import re
import tempfile
import subprocess
import collections as c
import configparser
import markdown2 as mk2
import pickle
import PyPDF4 as pdf
import wi_code.org_info as oi
import weasyprint as wp


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

<body class="flower_page" style="background-color:rgb({flower_color})">
<div id="{flower_name}" class="wi_{orientation}_page"
 style="{text_color}background-image: url({image_url});">
{{nav_bar}}
<div class="flower_box" style="background-color:rgba({flower_color}, .75); {box_side}:0in;">
{box_html}
</div>
<div class="picture_link" style="background-color:rgba({flower_color}, .75);">
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
toc_sub = """  - <a href="{page_loc}" name="{flower_ident}">{flower_name}</a>"""
toc_main_tex = """\item {poem_name}"""
toc_sub_tex = """\item \hyperref[{page_loc}]{{flower_name}}"""

outer_html = """
<head>
<link rel="stylesheet" href="./css/prepost_main.css"/>
<title>Table of contents</title>
</head>

<body class="{page_type}">
{formatted_markdown}
</body>

"""
outer_tex = """
\subsection{{{page_title}}} \label{{{page_ref}}}

{formatted_markdown}
"""

inner_html = """
<head>
<link rel="stylesheet" href="./css/prepost_main.css"/>
<title>{page_title}</title>
</head>

<body class="{page_type}">
<a href="./index.html">table of contents</a>

{formatted_markdown}

<a href="./index.html">table of contents</a>
</body>

"""
inner_tex = """
\subsection{{{page_title}}} \label{{{page_ref}}}

{formatted_markdown}
"""


inner_gloss_link = """
<a href="./glossary.html#{term}" title="{definition}" class="subtle_link">{disp_term}</a>
"""

post_item_templ = """
1. <a href="{item_path}">{item_name}</a>
"""
post_item_templ_tex = """
\item \hyperref[{item_path}]{{{item_name}}}
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
toc_template_tex = """
{summary_statement}

\clearpage 

\toc
\subsection{{Table of contents}}

{pre_items}

\subsubsection{{The Wild Iris}}
{items}

\subsubsection{{Appendix}}
{post_items}
"""

glossary_template = """
# Glossary

{items}

"""
glossary_template_tex = """
\subsection{{Glossary}} \label{{glossary}}

{items}
"""

glossary_line = """
**{term} <a name="{term}"></a>** - {definition}
"""
glossary_tex_line = """
\\textbf{{term}} - {definition}
"""

sources_template = """
# References

<ol>
{items}
</ol>

"""
sources_tex_template = """
\subsection{{References}}

\\begin{{itemize}}
{items}
\end{{itemize}}
"""

itemize_template = """
\\begin{{itemize}}
{items}
\end{{itemize}}
"""
enumerate_template = """
\\begin{{enumerate}}
{items}
\end{{enumerate}}
"""

source_line = """
<li>{fs} <a name="{ind}"></a></li>
"""
source_tex_line = """
\item {fs} \label{ind}
"""

img_pdf_options_vert = {
    "page-height": "8.5in",
    "page-width": "5.5in",
}

img_pdf_options_horiz = {
    "page-height": "8.5in",
    "page-width": "11in",
    "page-orientation": "Landscape",
}

img_pdf_options = {
    "margin-top": "0in",
    "margin-right": "0in",
    "margin-bottom": "0in",
    "margin-left": "0in",
    "encoding": "UTF-8",
    "custom-header": [("Accept-Encoding", "gzip")],
    "no-outline": None,
    "enable-local-file-access": None,
}


swap_list = (("-", " "), ("@", "'"))


def format_flower_name(s, make_swaps=swap_list):
    for old, new in swap_list:
        s = s.replace(old, new)
    s = s.title()
    if s == "Jacob'S Ladder":
        s = "Jacob's Ladder"
    return s


def _generate_format_source(source):
    if source == "encyclopedia":
        fs = (
            "Brickell, Christopher. American horticultural society "
            "encyclopedia of plants and flowers. Penguin, 2011."
        )
    elif len(source) > 0:
        fs = source
    else:
        fs = None
    return fs


def format_sources(txt, sources):
    new_sources = txt.split(",")
    links = []
    for ns in new_sources:
        out = sources.get(ns)
        if out is None:
            ind = len(sources) + 1
            fs = _generate_format_source(ns)

            if fs is not None:
                sources[ns] = ind, fs
        else:
            ind, fs = out
        vis_txt = "[{}]".format(ind)
        link = '<a title="{fs}" href="./references.html#{ind}">{vt}</a>'.format(
            ind=ind,
            vt=vis_txt,
            fs=fs,
        )
        links.append(link)
    sources = ",".join(links)
    return sources


ordered_fields = (
    "Other names",
    "Family",
    "Type",
    "Blooming period",
    "Sun requirement",
    "Soil requirement",
)
last_fields = ("Notes", "Sources",)


def _make_additional_fields(fields, poem_key):
    flower_name = poem_key.split('_')[0]
    new_fields = tuple(
        f for f in fields if re.match(flower_name + '_[0-9]+', f) is None
    )
    return new_fields


def format_detail(
    info,
    poem_key,
    poem_name,
    ordered_fields=ordered_fields,
    detail_template=detail_template,
    last_fields=last_fields,
    sources=None,
    glossary=None,
):
    if sources is None:
        sources = c.OrderedDict()
    ordered_lower = list(of.lower() for of in ordered_fields + last_fields)
    additional_fields = set(info.keys()).difference(ordered_lower)
    additional_fields = _make_additional_fields(additional_fields, poem_key)
    field_order = ((poem_key,) + ordered_fields + tuple(additional_fields) +
                   tuple(last_fields))
    out_str = ""
    for field in field_order:
        txt = info.get(field)
        if txt is not None:
            add_break = False
            if field == "Sources":
                txt = format_sources(txt, sources)
            elif field == poem_key:
                pg_num = field.split('_')[1]
                field = '_{}_ (page {})'.format(poem_name, pg_num)
                add_break = True
            elif field == "Type" and glossary is not None:
                txt = link_glossary(txt, glossary)
            add_str = detail_template.format(title=field, info=txt)
            out_str = out_str + add_str + "\n"
            if add_break:
                out_str = out_str + "<hr>\n"
    return out_str, sources


def make_page(
    folder,
    flower,
    poem_name,
    poem_page,
    file_suffix=".info",
    picture_folder="formatted_pictures/{templ}/",
    color_file="formatted_pictures/{templ}/color.pkl",
    use_gloss=oi.glossary,
    sources=None,
):
    """
    this reads a particular set of files and formats them into a markdown
    string for conversion to html or latex
    """
    main_info = os.path.join(folder, flower) + file_suffix
    poem_key = flower + '_{}'.format(poem_page)
    add_info = os.path.join(folder, poem_key) + file_suffix

    flower_name = format_flower_name(flower)
    parser = read_info(main_info, add_info, folder=folder)
    detail, sources = format_detail(
        parser["info"],
        poem_key,
        poem_name,
        sources=sources,
        glossary=use_gloss,
    )
    page_txt = main_template.format(flower_name=flower_name, detail=detail)
    page_html = mk2.markdown(page_txt)

    pic_file = parser["picture"].get("path")
    orientation = parser["picture"].get("orientation")
    if orientation is None:
        orientation = "horizontal"
    p_source_link = parser["picture"].get("source_url")
    p_source_text = parser["picture"].get("source_text")

    box_side = parser["picture"].get("box_side", "left")
    white_text = parser["picture"].getboolean("white_text", False)
    if white_text:
        text_color = "color: white; "
    else:
        text_color = ""

    flower_folder = picture_folder.format(templ=flower)
    flower_pic = os.path.join(flower_folder, pic_file)
    col_file = open(color_file.format(templ=flower), "rb")
    flower_col = pickle.load(col_file)

    page = page_template.format(
        flower_name=flower_name,
        image_url=flower_pic,
        flower_color=flower_col,
        box_html=page_html,
        orientation=orientation,
        pic_source_link=p_source_link,
        pic_source_text=p_source_text,
        poem_name=poem_name,
        box_side=box_side,
        text_color=text_color,
    )

    page_name = poem_key + ".html"
    return flower_name, page_name, page, flower_col, sources


def link_glossary(html, term_dict, repl_templ=inner_gloss_link):
    replacements = []
    for term, definition in term_dict.items():
        pattern = "(semi-)?{term}[,s)]?".format(term=term)
        term_re = re.compile(pattern, re.I)
        m = re.search(term_re, html)
        definition = "{}: {}".format(term, definition.replace('\n', ''))
        if m is not None:
            repl_str = m.group()
            new_str = repl_templ.format(
                term=term, disp_term=repl_str, definition=definition
            )
            goofy = str(hash(repl_str))
            html = html.replace(repl_str, goofy)
            replacements.append((goofy, new_str))
    for r_s, n_s in replacements:
        html = html.replace(r_s, n_s.strip('\n'))
    return html


def make_tex(
    folder,
    output_folder=None,
    use_toc=oi.toc,
    use_gloss=oi.glossary,
    use_post_toc=oi.post_toc,
    use_pre_toc=oi.pre_toc,
    toc_template=toc_template_tex,
    toc_main=toc_main,
    toc_sub=toc_sub,
    tex_fname="combined.tex",
    toc_tex_templ=outer_tex,
    gloss_line_templ=glossary_line,
    gloss_mkd_templ=glossary_template_tex,
    gloss_tex_templ=inner_tex,
    summary_statement_file="summary_statement.md",
    source_line_templ=source_tex_line,
    source_mkd_templ=sources_tex_template,
    source_html_templ=inner_tex,
    post_item_templ=post_item_templ_tex,
    pre_item_templ=post_item_templ_tex,
    pre_item_html_templ=inner_tex,
    **kwargs
        ):
    if output_folder is None:
        output_folder = folder
    new_color_file = os.path.join(
        output_folder, "formatted_pictures/{templ}/color.pkl"
    )
    sources = {}
    toc_lines = []
    write_later = []
    page_paths = {'pre': [], 'main': [], 'post': []}
    for (poem_name, poem_page), flowers in use_toc.items():
        toc_lines.append(toc_main.format(poem_name=poem_name))
        flower_entries = []
        for flower in flowers:
            out = make_page(
                folder,
                flower,
                poem_name,
                poem_page,
                sources=sources,
                color_file=new_color_file,
                **kwargs
            )
            flower_name, page_name, page, flower_color, sources = out

            page_loc = page_name.format(pg_num=poem_page)
            write_later.append((page_loc, poem_name, flower_name, page, flower_color))
            flower_ident = page_name.split(".")[0]
            toc_entry = toc_sub.format(flower_name=flower_name, page_loc=page_loc,
                                       flower_ident=flower_ident)
            flower_entries.append(toc_entry)
        toc_group = itemize_template.format(
               items="\n".join(flower_entries)
        )
        toc_lines.append(toc_group)
    main_items = "\n".join(toc_lines)
    main_items = enumerate_template.format(
        items=main_items
    )
    
    for i, page_info in enumerate(write_later):
        (curr_path, curr_pname, curr_fname, curr_page, flower_color) = page_info
        flower_ident = curr_path.split(".")[0]
        nav_bar = ""
        curr_page_f = curr_page.format(nav_bar=nav_bar, poem_name=curr_pname)
        fp = os.path.join(output_folder, curr_path)
        with open(fp, "wt") as f:
            f.write(curr_page_f)
        page_paths['main'].append(fp)

    post_toc_lines = []
    for section_name, link in use_post_toc.items():
        item = post_item_templ.format(item_name=section_name, item_path=link)
        post_toc_lines.append(item)
    post_items = "\n".join(post_toc_lines)
    post_items = enumerate_template.format(
        items=post_items
    )

    pre_toc_lines = []
    for section_name, link in use_pre_toc.items():
        item = pre_item_templ.format(item_name=section_name, item_path=link)
        ht = mk2.markdown(open(link.replace("html", "md"), "r").read())
        full_ht = pre_item_html_templ.format(
            page_title=section_name, formatted_markdown=ht, page_ref=link,
        )
        fp = os.path.join(output_folder, link)
        with open(fp, "wt") as f:
            f.write(full_ht)
        page_paths['pre'].append(fp)
        pre_toc_lines.append(item)
    pre_items = "\n".join(pre_toc_lines)
    pre_items = enumerate_template.format(
        items=pre_items
    )

    summary_statement = open(summary_statement_file, "r").read()
    toc_html = mk2.markdown(
        toc_template.format(
            pre_items=pre_items,
            items=main_items,
            post_items=post_items,
            summary_statement=summary_statement,
        )
    )
    toc_full = toc_tex_templ.format(
        page_title="Table of Contents", formatted_markdown=toc_html, page_ref="toc",
    )

    gloss_lines = []
    for term, definition in use_gloss.items():
        gloss_lines.append(gloss_line_templ.format(term=term, definition=definition))
    gloss_mkd = gloss_mkd_templ.format(items="\n".join(gloss_lines))
    gloss_html = mk2.markdown(gloss_mkd)
    gloss_full = gloss_tex_templ.format(
        page_title="Glossary", page_ref="glossary", formatted_markdown=gloss_html
    )

    source_lines = []
    for _, (ind, fs) in sources.items():
        source_lines.append(source_line_templ.format(fs=fs, ind=ind))
    source_mkd = source_mkd_templ.format(items="\n".join(source_lines))
    source_html = mk2.markdown(source_mkd)
    source_full = source_html_templ.format(
        page_title="References", page_ref="references", formatted_markdown=source_html
    )
    pages = [toc_full, gloss_full, source_full]
    full_tex = "\n \clearpage \n".join(pages)
    fp = os.path.join(output_folder, tex_fname)
    with open(fp, "wt") as f:
        f.write(full_tex)

    return fp


def make_html(
    folder,
    output_folder=None,
    use_toc=oi.toc,
    use_gloss=oi.glossary,
    use_post_toc=oi.post_toc,
    use_pre_toc=oi.pre_toc,
    toc_template=toc_template,
    toc_main=toc_main,
    toc_sub=toc_sub,
    toc_html_templ=outer_html,
    toc_fname="index.html",
    gloss_line_templ=glossary_line,
    gloss_fname="glossary.html",
    gloss_mkd_templ=glossary_template,
    gloss_html_templ=inner_html,
    nav_bar_templ=nav_bar_template,
    end_nav_bar_templ=end_nav_bar_template,
    beg_nav_bar_templ=beg_nav_bar_template,
    summary_statement_file="summary_statement.md",
    source_fname="references.html",
    source_line_templ=source_line,
    source_mkd_templ=sources_template,
    source_html_templ=inner_html,
    post_item_templ=post_item_templ,
    pre_item_templ=post_item_templ,
    pre_item_html_templ=inner_html,
    **kwargs
):
    if output_folder is None:
        output_folder = folder
    new_color_file = os.path.join(
        output_folder, "formatted_pictures/{templ}/color.pkl"
    )
    sources = {}
    toc_lines = []
    write_later = []
    page_paths = {'pre': [], 'main': [], 'post': []}
    for (poem_name, poem_page), flowers in use_toc.items():
        toc_lines.append(toc_main.format(poem_name=poem_name))
        for flower in flowers:
            out = make_page(
                folder,
                flower,
                poem_name,
                poem_page,
                sources=sources,
                color_file=new_color_file,
                **kwargs
            )
            flower_name, page_name, page, flower_color, sources = out

            page_loc = page_name.format(pg_num=poem_page)
            write_later.append((page_loc, poem_name, flower_name, page, flower_color))
            flower_ident = page_name.split(".")[0]
            toc_lines.append(toc_sub.format(flower_name=flower_name, page_loc=page_loc,
                                            flower_ident=flower_ident))
    n_pages = len(write_later)
    for i, page_info in enumerate(write_later):
        (curr_path, curr_pname, curr_fname, curr_page, flower_color) = page_info
        flower_ident = curr_path.split(".")[0]
        toc_link = "index.html#{flower_ident}".format(flower_ident=flower_ident)
        if i == 0:
            next_path, next_pname, next_fname, next_page, _ = write_later[i + 1]
            nav_bar = beg_nav_bar_templ.format(
                toc_link=toc_link,
                next_link=next_path,
                curr_link=curr_path,
                flower_color=flower_color,
            )
        elif i == n_pages - 1:
            prev_path, prev_pname, prev_fname, prev_page, _ = write_later[i - 1]
            nav_bar = end_nav_bar_templ.format(
                toc_link=toc_link,
                prev_link=prev_path,
                curr_link=curr_path,
                flower_color=flower_color,
            )
        else:
            prev_path, prev_pname, prev_fname, prev_page, _ = write_later[i - 1]
            next_path, next_pname, next_fname, next_page, _ = write_later[i + 1]
            nav_bar = nav_bar_templ.format(
                toc_link=toc_link,
                prev_link=prev_path,
                next_link=next_path,
                flower_color=flower_color,
            )
        curr_page_f = curr_page.format(nav_bar=nav_bar, poem_name=curr_pname)
        fp = os.path.join(output_folder, curr_path)
        with open(fp, "wt") as f:
            f.write(curr_page_f)
        page_paths['main'].append(fp)

    post_toc_lines = []
    for section_name, link in use_post_toc.items():
        item = post_item_templ.format(item_name=section_name, item_path=link)
        post_toc_lines.append(item)
    post_items = "\n".join(post_toc_lines)

    pre_toc_lines = []
    for section_name, link in use_pre_toc.items():
        item = pre_item_templ.format(item_name=section_name, item_path=link)
        ht = mk2.markdown(open(link.replace("html", "md"), "r").read())
        full_ht = pre_item_html_templ.format(
            page_type="org_page", page_title=section_name, formatted_markdown=ht
        )
        fp = os.path.join(output_folder, link)
        with open(fp, "wt") as f:
            f.write(full_ht)
        page_paths['pre'].append(fp)
        pre_toc_lines.append(item)
    pre_items = "\n".join(pre_toc_lines)

    main_items = "\n".join(toc_lines)

    summary_statement = open(summary_statement_file, "r").read()
    toc_html = mk2.markdown(
        toc_template.format(
            pre_items=pre_items,
            items=main_items,
            post_items=post_items,
            summary_statement=summary_statement,
        )
    )
    toc_full = toc_html_templ.format(page_type="org_page", formatted_markdown=toc_html)
    fp = os.path.join(output_folder, toc_fname)
    with open(fp, "wt") as f:
        f.write(toc_full)
    page_paths['pre'].insert(0, fp)

    gloss_lines = []
    for term, definition in use_gloss.items():
        gloss_lines.append(gloss_line_templ.format(term=term, definition=definition))
    gloss_mkd = gloss_mkd_templ.format(items="\n".join(gloss_lines))
    gloss_html = mk2.markdown(gloss_mkd)
    gloss_full = gloss_html_templ.format(
        page_type="org_page", page_title="Glossary", formatted_markdown=gloss_html
    )
    fp = os.path.join(output_folder, gloss_fname)
    with open(fp, "wt") as f:
        f.write(gloss_full)
    page_paths['post'].append(fp)

    source_lines = []
    for _, (ind, fs) in sources.items():
        source_lines.append(source_line_templ.format(fs=fs, ind=ind))
    source_mkd = source_mkd_templ.format(items="\n".join(source_lines))
    source_html = mk2.markdown(source_mkd)
    source_full = source_html_templ.format(
        page_type="org_page", page_title="References", formatted_markdown=source_html
    )
    fp = os.path.join(output_folder, source_fname)
    with open(fp, "wt") as f:
        f.write(source_full)
    page_paths['post'].append(fp)
    return page_paths


def read_info(*fls, folder=""):
    parser = configparser.ConfigParser()
    _ = parser.read(list(os.path.join(folder, fl) for fl in fls))
    return parser


def get_num_pages(pdf_file):
    with open(pdf_file, 'rb') as f:
        r = pdf.PdfFileReader(f)
        n_pages = r.numPages
    return n_pages


def make_temp_css(css, folder, page_num, targ_string="/* REPLACE HERE */"):
    with open(css, 'r') as cf:
        txt = cf.read()
    repl_string = """
    counter-reset: page {pn};
    counter-increment: page;
    @top-right {{
        content: counter(page);
    }}
    z-index: 100;
    """
    repl_string = repl_string.format(pn=page_num)
    new_css = txt.replace(targ_string, repl_string)
    new_css_f = os.path.join(folder, "temp.css")
    with open(new_css_f, 'w') as ncf:
        ncf.write(new_css)
    return new_css_f


def _url_fetcher(url, *args, **kwargs):
    print(url)
    url = url.strip("file:")
    print(url)
    f = open(url, 'rb').read()
    print(url)
    out = {"string": f}
    return out


def make_pdf_groups(folder, paths, css, max_num=10, page_num=0):
    page_list = []
    if max_num is not None:
        paths = paths[:max_num]
    for html_path in paths:
        _, name_ext = os.path.split(html_path)
        name, ext = os.path.splitext(name_ext)
        # temp_css = make_temp_css(css, folder, page_num)
        temp_css = css
        out_path = os.path.join(folder, name + ".pdf")
        p_html = wp.HTML(filename=html_path, url_fetcher=_url_fetcher)
        p_html.write_pdf(target=out_path, stylesheets=(temp_css,))
        page_list.append(out_path)
        page_num += get_num_pages(out_path)
    return page_list, page_num


def make_tex_groups(html_pages, tf, css):
    tex_fragments = []
    pattern = "\\\\begin\{document\}(?P<main>.*)\\\end\{document\}"
    pattern = re.compile(pattern, flags=re.DOTALL)
    for page in html_pages:
        _, name = os.path.split(page)
        name, _ = os.path.splitext(name)
        new_path = os.path.join(tf, name + ".tex")
        subprocess.run(["pandoc", page, "-s", "-o", new_path])
        tex = open(new_path, "r").read()
        m = re.search(pattern, tex)
        fragment = m.groups("main")[0]
        tex_fragments.append(fragment)
    tg = "\clearpage".join(tex_fragments)
    return tg


def make_tex_and_pdf(
        trunk, pre_tex, pages, post_tex, template="wi_code/latex_template.tex",
):
    template_tex = open(template, "r").read()

    include_pages = list("\includepdf{p}".format(p=page) for page in pages)
    include_pages = "\n".join(include_pages)
    fl = template_tex.format(
        pre_pages=pre_tex, include_pages=include_pages, end_pages=post_tex,
    )
    
    tex_path = trunk + ".tex"
    open(tex_path, "w").write(fl)
    subprocess.run(["pdflatex", tex_path])


def make_all_pdfs(
        page_paths,
        main_css,
        prepost_css,
        out_folder,
        filename="a_botanical_companion",
        pages_folder=None,
        tex_template="wi_code/latex_template.tex",
):
    with tempfile.TemporaryDirectory() as tf:
        if pages_folder is not None:
            tf = pages_folder
        pre_tex_format = make_tex_groups(page_paths["pre"], tf, prepost_css)
        
        pages, page_nums = make_pdf_groups(
            tf, page_paths["main"], main_css, 
        )

        post_tex_format = make_tex_groups(
            page_paths["post"], tf, prepost_css,
        )

        trunk = os.path.join(out_folder, filename)
        make_tex_and_pdf(trunk, pre_tex_format, pages, post_tex_format)
