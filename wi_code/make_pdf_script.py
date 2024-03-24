import os
import shutil
import argparse

import wi_code.read_format as rf
import wi_code.image_display as img


def create_parser():
    parser = argparse.ArgumentParser(
        description="generate the html for the botanical companion"
    )
    parser.add_argument("-i", "--information_folder", default=".")
    parser.add_argument("-o", "--output_folder", default=".")

    parser.add_argument("--resave_images", default=False, action="store_true")
    parser.add_argument("--make_pdf", default=False, action="store_true")
    parser.add_argument("--resave_pdfs", default=False, action="store_true")
    parser.add_argument("--lazy_compile", default=False, action="store_true")
    return parser


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    if not os.path.isdir(args.output_folder):
        os.mkdir(args.output_folder)
    o_css = os.path.join(args.information_folder, "css")
    n_css = os.path.join(args.output_folder, "css")
    shutil.copytree(o_css, n_css, dirs_exist_ok=True)

    formatted_pic_folder = os.path.join(args.output_folder, "formatted_pictures")
    images_exist = os.path.isdir(formatted_pic_folder)
    if args.resave_images or not images_exist:
        img.resave_images(args.information_folder, out_folder=formatted_pic_folder)

    page_path = rf.make_tex(
        args.information_folder,
        output_folder=args.output_folder,
        resave_pdfs=args.resave_pdfs,
    )
    if args.lazy_compile:
        n_times = 1
    else:
        n_times = 2
    rf.compile_latex(page_path, n_times=n_times)
