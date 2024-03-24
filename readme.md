# A botanical companion to _The Wild Iris_

This code (and included images) can be used to generate both the [web](https://wj2.github.io/wild_iris/) and [pdf](https://wj2.github.io/wild_iris/a_botanical_companion_to_the-wild-iris.pdf) versions of the zine A botanical companion to The Wild Iris. 

## Dependencies
The repository relies on a few external packages:
* numpy
* Pillow
* matplotlib
* markdown2
* weasyprint

as well as on many core python packages. 

## Usage
### Web version
To generate the web version of the zine in FOLDER, run:
```
python -m wi_code.make_website_script --output_folder FOLDER
```
from this directory. Once it completes,
`FOLDER/index.html`
will then be the root page of the zine. 

### PDF version
To generate the pdf version of the zine in FOLDER, run:
```
python -m wi_code.make_pdf_script --output_folder FOLDER
```
from this directory. Once it completes
`FOLDER/a_botanical_companion_to_the-wild-iris.pdf`
will be the pdf version of the zine. The pdf version of the zine additionally requires that latex is installed and `pdflatex` is on the path. 
