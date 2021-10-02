# encoding: utf-8
import os
from io import BytesIO

import piexif
from PIL import Image, ImageFile

from .data_structures import Task, TaskResult
from .img_aux_processing import downsize_img, make_grayscale, save_compressed


def optimize_webp(task: Task) -> TaskResult:
    """ tbd

    :param task: A Task object containing all the parameters for the image processing.
    :return: A TaskResult object containing information for single file report.
    """
    img: Image.Image = Image.open(task.src_path)
    orig_format = img.format
    orig_mode = img.mode

    orig_size = os.path.getsize(task.src_path)
    orig_colors, final_colors = 0, 0

    result_format = "WEBP"
    try:
        had_exif = True if piexif.load(task.src_path)['Exif'] else False
    except piexif.InvalidImageDataError:  # Not a supported format
        had_exif = False
    except ValueError:  # No exif info
        had_exif = False
    # TODO: Check if we can provide a more specific treatment of piexif exceptions.
    except Exception:
        had_exif = False

    if task.max_w or task.max_h:
        img, was_downsized = downsize_img(img, task.max_w, task.max_h)
    else:
        was_downsized = False

    if task.grayscale:
        img = make_grayscale(img)

    tmp_buffer = BytesIO()  # In-memory buffer
    try:
        img.save(
            tmp_buffer,
            optimize=True,
            format=result_format)
    except IOError:
        ImageFile.MAXBLOCK = img.size[0] * img.size[1]
        img.save(
            tmp_buffer,
            optimize=True,
            format=result_format)

    if task.keep_exif and had_exif:
        try:
            piexif.transplant(os.path.expanduser(task.src_path), tmp_buffer)
            has_exif = True
        except ValueError:
            has_exif = False
        # TODO: Check if we can provide a more specific treatment
        #       of piexif exceptions.
        except Exception:
            had_exif = False
    else:
        has_exif = False

    img_mode = img.mode
    img.close()
    compare_sizes = not task.no_size_comparison

    base_path = os.path.splitext(task.src_path)[0]
    target_path = f"{base_path}.webp"

    was_optimized, final_size = save_compressed(task.src_path,
                                                tmp_buffer,
                                                compare_sizes,
                                                output_path=target_path)

    return TaskResult(task.src_path, orig_format, result_format, orig_mode,
                      img_mode, orig_colors, final_colors, orig_size,
                      final_size, was_optimized, was_downsized, had_exif,
                      has_exif, task.output_config)
