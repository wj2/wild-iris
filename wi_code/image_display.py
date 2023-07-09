
import os
import re
import configparser
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from PIL import Image
import pickle

import wi_code.read_format as rf

def get_images(folder, template='.*\.info$', image_folder='pictures',
               info_key='picture'):
    fls = os.listdir(folder)
    for fl in fls:
        m = re.match(template, fl)
        if m is not None:
            info = rf.read_info(fl, folder)
            img_info = info[info_key]
            pic_file = img_info.get('path')
            pic_folder, _ = os.path.splitext(fl)
            pic_path = os.path.join(image_folder, pic_folder, pic_file)
            img = Image.open(pic_path)
            yield (img_info, img)

            
def resave_images(folder, template='.*\.info$', image_folder='pictures',
                  info_key='picture', out_folder='formatted_pictures',
                  color_file='color.pkl'):
    if not os.path.isdir(out_folder):
        os.mkdir(out_folder)
    fls = os.listdir(folder)
    for fl in fls:
        m = re.match(template, fl)
        if m is not None:
            info = rf.read_info(fl, folder)
            img_info = info[info_key]
            pic_file = img_info.get('path')
            orientation = img_info.get('orientation')
            pic_folder, _ = os.path.splitext(fl)
            pic_path = os.path.join(image_folder, pic_folder, pic_file)
            img = Image.open(pic_path)
            out = get_crop_box(img_info, img.size)
            box_lb, h_len, v_len, resize_targ = out
            
            crop_img = img.crop(box=(box_lb[0], box_lb[1],
                                     box_lb[0] + h_len, box_lb[1] + v_len))
            crop_img = crop_img.resize(resize_targ)
            img_arr = np.asarray(img)
            print(fl, info)
            if info is not None:
                pt = _convert_list(img_info.get('color_point'), typefunc=int)
            else:
                pt = (0, 0)
            print(pt)
            col = ','.join(str(num) for num in img_arr[pt[1], pt[0]][:3])
            print(col)
            new_folder = os.path.join(out_folder, pic_folder)
            if not os.path.isdir(new_folder):
                os.mkdir(new_folder)
            crop_img.save(os.path.join(new_folder, pic_file))
            pickle.dump(col, open(os.path.join(new_folder, color_file), 'wb'))
            print(new_folder)


def check_images(folder, **kwargs):
    for (info, img) in get_images(folder, **kwargs):
        print(info.get('path'))
        f, ax = plot_img(img, info)
        plt.show(block=True)

def _convert_list(in_str, typefunc=int):
    if in_str is None or len(in_str.split(',')) <= 1:
        out = (0, 0)
    else:
        out = tuple(typefunc(x) for x in in_str.split(','))
    return out

def get_crop_box(info, img_size, horizontal=True, aspect_ratio=8.5/11,
                 aspect_ratio_vert=5.5/8.5, dpi=100):
    if info is not None:
        box_lb = _convert_list(info.get('crop_window'), typefunc=int)
        box_scale = info.getfloat('window_scale')
        if box_scale is None:
            box_scale = 1
        orientation = info.get('orientation')
        if orientation is not None:
            horizontal = not (orientation == 'vertical')
        center = info.get('center')
        if center is not None:
            box_lb = (0, 0)
    else:
        box_lb = (0, 0)
        box_scale = 1
        pt = (0, 0)
        center = None
        
    h_dim, v_dim = img_size
    h_r, v_r = h_dim - box_lb[0], v_dim - box_lb[1]
    if horizontal:
        ar = aspect_ratio
        resize_targ = (11*dpi, int(8.5*dpi))
    else:
        ar = 1/aspect_ratio_vert
        resize_targ = (int(5.5*dpi), int(8.5*dpi))
    h_len, v_len = get_lens(h_r, v_r, ar, box_scale)
    if center is not None:
        box_lb = get_center_box(h_len, v_len, h_r, v_r, center)
    return box_lb, h_len, v_len, resize_targ

def plot_img(img, info=None, ax=None, fwid=8, horizontal=True,
             aspect_ratio=8.5/11, use_info=False, aspect_ratio_vert=5.5/8.5,
             save_folder=None):
    if ax is None:
        f, (ax_img, ax_col) = plt.subplots(1, 2, figsize=(2*fwid, fwid))
    ax_img.imshow(img)
    box_lb, h_len, v_len, _ = get_crop_box(info, img.size, horizontal=horizontal,
                                           aspect_ratio=aspect_ratio,
                                           aspect_ratio_vert=aspect_ratio_vert)
            
    rect = patches.Rectangle(box_lb, h_len, v_len, linewidth=1,
                             edgecolor='r', facecolor='none')
    ax_img.add_patch(rect)
    if info is not None:
        pt = _convert_list(info.get('color_point'), typefunc=int)
    else:
        pt = (0, 0)

    img_arr = np.asarray(img)
    ## might want to resize along with cropping
    ## could add here
    ## NOT WORKING CORRECTLY, TEST MORE
    ax_col.imshow(img_arr[pt[1]:pt[1]+1, pt[0]:pt[0]+1])
    ax_img.plot([pt[0]], [pt[1]], 'o')
    f.suptitle(img.filename)
    return f, ax

def get_lens(h_r, v_r, aspect_ratio, box_scale=1):
    h_len = box_scale*h_r
    v_len = aspect_ratio*h_len
    if v_len > v_r:
        box_scale = v_r/v_len
    h_len = box_scale*h_r
    v_len = aspect_ratio*h_len
    print(h_r, h_len)
    print(v_r, v_len)
    print(h_len / v_len, v_len / h_len)
    return h_len, v_len

def _get_mid(val, val_max):
    return int(round((val_max - val)/2))

def get_center_box(h, v, h_max, v_max, center):
    center = center.replace('center', 'middle')
    v_c, h_c = center.split(' ')
    if h_c == 'left':
        box_h = 0
    elif h_c == 'middle':
        mid = _get_mid(h, h_max)
        box_h = mid
    elif h_c == 'right':
        mid = _get_mid(h, h_max)
        box_h = 2*mid
    else:
        raise IOError('left key {} not recognized'.format(h_c))
    if v_c == 'top':
        box_v = 0
    elif v_c == 'middle':
        mid = _get_mid(v, v_max)
        box_v = mid
    elif v_c == 'bottom':
        mid = _get_mid(v, v_max)
        box_v = 2*mid
    else:
        raise IOError('left key {} not recognized'.format(h_c))
    return (box_h, box_v)
