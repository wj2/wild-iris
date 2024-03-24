
full_tex_template = """
\documentclass[letter,landscape,12pt,twocolumn]{{article}}
\\usepackage{{setspace}}
\\usepackage{{hyperref}}
\\usepackage{{autonum}}
\\usepackage{{enumitem}}
\\usepackage{{titlesec}}
\\usepackage{{parskip}}
\\usepackage{{tikz}}
\\usepackage{{siunitx}}
\\usepackage{{titletoc}}
\\usepackage{{authblk}}
\\usepackage{{lineno}}
\\usepackage[margin=0.75in]{{geometry}}
\cslet{{blx@noerroretextools}}\empty
\\usepackage[style=nature]{{biblatex}}
\\usepackage{{ccaption}}
\\usepackage[font=footnotesize,labelfont=bf]{{caption}}
\\usepackage{{pdfpages}}
\providecommand{{\\tightlist}}{{%
  \setlength{{\itemsep}}{{0pt}}\setlength{{\parskip}}{{0pt}}}}


\\title{{A botanical companion to The Wild Iris}}
\\author{{Jeff Johnston}}

\\setcounter{{section}}{{1}}
\\begin{{document}}

-
\includepdf{{cover.pdf}}

{everything}

\end{{document}}
"""

pdf_include = """
\phantomsection
\\addcontentsline{{toc}}{{subsubsection}}{{{flower_name}}}
\includepdf{{{p}}}
\label{{{ref}}}
"""

poem_toc = """
\phantomsection
\\addcontentsline{{toc}}{{subsection}}{{{poem_name}}}
\label{{{poem_ident}}}
"""

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
inner_gloss_link = """
<a href="./glossary.html#{term}" title="{definition}" class="subtle_link">{disp_term}</a>
"""
inner_gloss_link_tex = """
{disp_term}
"""

inner_tex = """
\subsection{{{page_title}}} \label{{{page_ref}}}

{formatted_markdown}
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

\\tableofcontents
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

\\begin{{enumerate}}
{items}
\end{{enumerate}}
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
\item {fs} \label{{{ind}}}
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

