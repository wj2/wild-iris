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
import urllib as url

from wi_code.text_snippets import *


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


def format_sources(txt, sources, make_links=True):
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
        if make_links:
            link = '<a title="{fs}" href="./references.html#{ind}">{vt}</a>'.format(
                ind=ind,
                vt=vis_txt,
                fs=fs,
            )
        else:
            link = vis_txt
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
last_fields = (
    "Notes",
    "Sources",
)


def _make_additional_fields(fields, poem_key):
    flower_name = poem_key.split("_")[0]
    new_fields = tuple(
        f for f in fields if re.match(flower_name + "_[0-9]+", f) is None
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
    make_links=True,
):
    if sources is None:
        sources = c.OrderedDict()
    ordered_lower = list(of.lower() for of in ordered_fields + last_fields)
    additional_fields = set(info.keys()).difference(ordered_lower)
    additional_fields = _make_additional_fields(additional_fields, poem_key)
    field_order = (
        (poem_key,) + ordered_fields + tuple(additional_fields) + tuple(last_fields)
    )
    out_str = ""
    for field in field_order:
        txt = info.get(field)
        if txt is not None:
            add_break = False
            if field == "Sources":
                txt = format_sources(txt, sources, make_links=make_links)
            elif field == poem_key:
                pg_num = field.split("_")[1]
                field = "_{}_ (page {})".format(poem_name, pg_num)
                add_break = True
            elif field == "Type" and glossary is not None:
                txt = link_glossary(txt, glossary, make_links=make_links)
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
    make_links=True,
):
    """
    this reads a particular set of files and formats them into a markdown
    string for conversion to html or latex
    """
    main_info = os.path.join(folder, flower) + file_suffix
    poem_key = flower + "_{}".format(poem_page)
    add_info = os.path.join(folder, poem_key) + file_suffix

    flower_name = format_flower_name(flower)
    parser = read_info(main_info, add_info, folder=folder)
    detail, sources = format_detail(
        parser["info"],
        poem_key,
        poem_name,
        sources=sources,
        glossary=use_gloss,
        make_links=make_links,
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


def link_glossary(
    html,
    term_dict,
    repl_templ=inner_gloss_link,
    make_links=True,
    repl_no_link_templ=inner_gloss_link_tex,
):
    replacements = []
    for term, definition in term_dict.items():
        pattern = "(semi-)?{term}[,s)]?".format(term=term)
        term_re = re.compile(pattern, re.I)
        m = re.search(term_re, html)
        definition = "{}: {}".format(term, definition.replace("\n", ""))
        if m is not None:
            repl_str = m.group()
            if make_links:
                new_str = repl_templ.format(
                    term=term, disp_term=repl_str, definition=definition
                )
            else:
                new_str = repl_no_link_templ.format(disp_term=repl_str)
            goofy = str(hash(repl_str))
            html = html.replace(repl_str, goofy)
            replacements.append((goofy, new_str))
    for r_s, n_s in replacements:
        html = html.replace(r_s, n_s.strip("\n"))
    return html


def md_to_tex(text, out="temp.tex", orig="temp_orig.md"):
    with tempfile.TemporaryDirectory() as tf:
        file = os.path.join(tf, orig)
        with open(file, "w") as f:
            f.write(text)

        new_path = os.path.join(tf, out)
        arg = [
            "pandoc",
            "--read",
            "markdown",
            "--write",
            "latex",
            "--output",
            new_path,
            file,
        ]
        subprocess.run(arg)
        new_text = open(new_path, "r").read()
    return new_text


def _format_tex_link(s):
    s = s.strip()
    elements = list(filter(lambda x: len(x) > 0, s.split(" ")))
    if len(elements) == 1:
        info = url.parse.urlparse(s.strip())
        if info.netloc == "en.wikipedia.org":
            plant = info.path.split("/")[-1]
            face = "Wikipedia: {}".format(plant.replace("_", " "))
        elif info.netloc == "gobotany.nativeplanttrust.org":
            face = "Native Plant Trust"
        elif info.netloc == "www.chicagobotanic.org":
            face = "Chicago Botanical Garden"
        elif info.path[-3:] == "pdf":
            face = info.path.split("/")[-1].split(".")[0]
            face = face.replace("-", " ")
        else:
            face = s
        entry = "\href{{{link}}}{{{face}}}".format(link=s, face=face)
    else:
        entry = s
    return entry


def md_to_tex_file(
    file,
    out="temp.tex",
):
    with tempfile.TemporaryDirectory() as tf:
        new_path = os.path.join(tf, out)
        arg = [
            "pandoc",
            "--read",
            "markdown",
            "--write",
            "latex",
            "--output",
            new_path,
            file,
        ]
        subprocess.run(arg)
        new_text = open(new_path, "r").read()
    return new_text


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
    tex_fname="a_botanical_companion_to_the-wild-iris.tex",
    toc_tex_templ=outer_tex,
    gloss_line_templ=glossary_line,
    gloss_mkd_templ=glossary_template_tex,
    gloss_tex_templ=inner_tex,
    summary_statement_file="summary_statement.md",
    version_statement_file="web_version.md",
    source_line_templ=source_tex_line,
    source_mkd_templ=sources_tex_template,
    source_html_templ=inner_tex,
    post_item_templ=post_item_templ_tex,
    pre_item_templ=post_item_templ_tex,
    pre_item_html_templ=inner_tex,
    main_css="css/main.css",
    resave_pdfs=False,
    include_template=pdf_include,
    latex_template=full_tex_template,
    **kwargs
):
    if output_folder is None:
        output_folder = folder
    new_color_file = os.path.join(output_folder, "formatted_pictures/{templ}/color.pkl")
    sources = {}
    include_list = []
    for (poem_name, poem_page), flowers in use_toc.items():
        poem_ident = "{}_{}".format(poem_name, poem_page)
        include_list.append(poem_toc.format(poem_name=poem_name, poem_ident=poem_ident))

        for flower in flowers:
            out = make_page(
                folder,
                flower,
                poem_name,
                poem_page,
                sources=sources,
                color_file=new_color_file,
                make_links=False,
                **kwargs
            )
            flower_name, page_name, page, flower_color, sources = out

            page_loc = page_name.format(pg_num=poem_page)
            flower_ident = page_name.split(".")[0]

            nav_bar = ""
            curr_page_f = page.format(nav_bar=nav_bar, poem_name=poem_name)
            fp = os.path.join(output_folder, page_loc)
            with open(fp, "wt") as f:
                f.write(curr_page_f)
            p_html = wp.HTML(filename=fp, url_fetcher=_url_fetcher)
            out_path = fp.replace("html", "pdf")
            if not os.path.isfile(out_path) or resave_pdfs:
                p_html.write_pdf(target=out_path, stylesheets=(main_css,))

            inc = pdf_include.format(
                flower_name=flower_name, p=out_path, ref=flower_ident
            )
            include_list.append(inc)

    plant_page_full = "\n".join(include_list)

    post_toc_lines = []
    for section_name, link in use_post_toc.items():
        item = post_item_templ.format(item_name=section_name, item_path=link)
        post_toc_lines.append(item)
    post_items = "\n".join(post_toc_lines)
    post_items = enumerate_template.format(items=post_items)

    pre_toc_lines = []
    for section_name, link in use_pre_toc.items():
        item = pre_item_templ.format(item_name=section_name, item_path=link)
        full_ht = md_to_tex_file(link.replace("html", "md"))
        pre_toc_lines.append(full_ht)
    pre_full = "\n".join(pre_toc_lines)

    summary_statement = md_to_tex_file(summary_statement_file)
    version_statement = md_to_tex_file(version_statement_file)
    summary_statement = "\n\n".join((summary_statement, version_statement))
    pre_full = "{}\n \clearpage {}".format(summary_statement, pre_full)
    toc_full = toc_template.format(
        summary_statement="",
    )

    gloss_lines = []
    for term, definition in use_gloss.items():
        gloss_lines.append(gloss_line_templ.format(term=term, definition=definition))
    gloss_mkd = gloss_mkd_templ.format(items="\n".join(gloss_lines))
    gloss_full = md_to_tex(gloss_mkd)

    source_lines = []
    for _, (ind, fs) in sources.items():
        fs_use = _format_tex_link(fs)
        line = source_line_templ.format(fs=fs_use, ind=ind)
        line = line.replace("_", "\_")
        source_lines.append(line)
    source_mkd = source_mkd_templ.format(items="\n".join(source_lines))
    source_full = md_to_tex(source_mkd)
    pages = [
        pre_full,
        toc_full,
        "\section{A botanical companion to \emph{The~Wild~Iris}}",
        plant_page_full,
        "\section{Appendix}",
        gloss_full,
        source_full,
    ]
    combined_tex = "\n \clearpage \n".join(pages)
    fp = os.path.join(output_folder, tex_fname)
    full_tex = latex_template.format(everything=combined_tex)
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
    version_statement_file="pdf_version.md",
    practical_note_file="practical_note.md",
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
    new_color_file = os.path.join(output_folder, "formatted_pictures/{templ}/color.pkl")
    sources = {}
    toc_lines = []
    write_later = []
    page_paths = {"pre": [], "main": [], "post": []}
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
            toc_lines.append(
                toc_sub.format(
                    flower_name=flower_name,
                    page_loc=page_loc,
                    flower_ident=flower_ident,
                )
            )
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
        page_paths["main"].append(fp)

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
        page_paths["pre"].append(fp)
        pre_toc_lines.append(item)
    pre_items = "\n".join(pre_toc_lines)

    main_items = "\n".join(toc_lines)

    summary_statement = open(summary_statement_file, "r").read()
    version_statement = open(version_statement_file, "r").read()
    summary_statement = "\n\n".join((summary_statement, version_statement))

    practical_note = open(practical_note_file, "r").read()
    summary_statement = "\n".join((summary_statement, practical_note))
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
    page_paths["pre"].insert(0, fp)

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
    page_paths["post"].append(fp)

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
    page_paths["post"].append(fp)
    return page_paths


def read_info(*fls, folder=""):
    parser = configparser.ConfigParser()
    _ = parser.read(list(os.path.join(folder, fl) for fl in fls))
    return parser


def get_num_pages(pdf_file):
    with open(pdf_file, "rb") as f:
        r = pdf.PdfFileReader(f)
        n_pages = r.numPages
    return n_pages


def make_temp_css(css, folder, page_num, targ_string="/* REPLACE HERE */"):
    with open(css, "r") as cf:
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
    with open(new_css_f, "w") as ncf:
        ncf.write(new_css)
    return new_css_f


def _url_fetcher(url, *args, **kwargs):
    print(url)
    url = url.strip("file:")
    print(url)
    f = open(url, "rb").read()
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


def compile_latex(
        fp,
        n_times=2,
):
    trunk, _ = os.path.split(fp)
    for i in range(n_times):
        subprocess.run(["pdflatex", "--output-directory", trunk, fp])
    name, _ = os.path.splitext(fp)
    file = name + ".pdf"
    return file


def make_tex_and_pdf(
    trunk,
    pre_tex,
    pages,
    post_tex,
    template="wi_code/latex_template.tex",
):
    template_tex = open(template, "r").read()

    include_pages = list("\includepdf{p}".format(p=page) for page in pages)
    include_pages = "\n".join(include_pages)
    fl = template_tex.format(
        pre_pages=pre_tex,
        include_pages=include_pages,
        end_pages=post_tex,
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
            tf,
            page_paths["main"],
            main_css,
        )

        post_tex_format = make_tex_groups(
            page_paths["post"],
            tf,
            prepost_css,
        )

        trunk = os.path.join(out_folder, filename)
        make_tex_and_pdf(trunk, pre_tex_format, pages, post_tex_format)
