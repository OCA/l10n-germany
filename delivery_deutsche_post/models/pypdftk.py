""" pypdftk

Python module to drive the awesome pdftk binary.
See http://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/

"""

import itertools
import logging
import os
import shutil
import subprocess
import tempfile

log = logging.getLogger(__name__)

if os.getenv("PDFTK_PATH"):
    PDFTK_PATH = os.getenv("PDFTK_PATH")
else:
    PDFTK_PATH = "/usr/bin/pdftk"
    if not os.path.isfile(PDFTK_PATH):
        PDFTK_PATH = "pdftk"


def check_output(*popenargs, **kwargs):
    if "stdout" in kwargs:
        raise ValueError("stdout argument not allowed, it will be overridden.")
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd, output=output)
    return output


def run_command(command, shell=False):
    """run a system command and yield output"""
    p = check_output(command, shell=shell)
    return p.split(b"\n")


def get_num_pages(pdf_path):
    """return number of pages in a given PDF file"""
    for line in run_command([PDFTK_PATH, pdf_path, "dump_data"]):
        if line.lower().startswith(b"numberofpages"):
            return int(line.split(b":")[1])
    return 0


def fill_form(pdf_path, datas=None, out_file=None, flatten=True):
    """
    Fills a PDF form with given dict input data.
    Return temp file if no out_file provided.
    """
    if datas is None:
        datas = {}
    cleanOnFail = False
    tmp_fdf = gen_xfdf(datas)
    handle = None
    if not out_file:
        cleanOnFail = True
        handle, out_file = tempfile.mkstemp()

    cmd = "%s %s fill_form %s output %s" % (PDFTK_PATH, pdf_path, tmp_fdf, out_file)
    if flatten:
        cmd += " flatten"
    try:
        run_command(cmd, True)
    except Exception:
        if cleanOnFail:
            os.remove(tmp_fdf)
        raise
    finally:
        if handle:
            os.close(handle)
    os.remove(tmp_fdf)
    return out_file


def dump_data_fields(pdf_path):
    """
    Return list of dicts of all fields in a PDF.
    """
    cmd = "%s %s dump_data_fields" % (PDFTK_PATH, pdf_path)
    # Either can return strings with :
    #    field_data = map(lambda x: x.decode("utf-8").split(': ', 1), run_command(cmd, True))
    # Or return bytes with : (will break tests)
    #    field_data = map(lambda x: x.split(b': ', 1), run_command(cmd, True))
    field_data = list(
        map(lambda x: x.decode("utf-8").split(": ", 1), run_command(cmd, True))
    )
    fields = [
        list(group)
        for k, group in itertools.groupby(field_data, lambda x: len(x) == 1)
        if not k
    ]
    return [dict(f) for f in fields]


def concat(files, out_file=None):
    """
    Merge multiples PDF files.
    Return temp file if no out_file provided.
    """
    cleanOnFail = False
    handle = None
    if not out_file:
        cleanOnFail = True
        handle, out_file = tempfile.mkstemp()
    if len(files) == 1:
        shutil.copyfile(files[0], out_file)
    args = [PDFTK_PATH]
    args += files
    args += ["cat", "output", out_file]
    try:
        run_command(args)
    except Exception:
        if cleanOnFail:
            os.remove(out_file)
        raise
    finally:
        if handle:
            os.close(handle)
    return out_file


def split(pdf_path, out_dir=None):
    """
    Split a single PDF file into pages.
    Use a temp directory if no out_dir provided.
    """
    cleanOnFail = False
    if not out_dir:
        cleanOnFail = True
        out_dir = tempfile.mkdtemp()
    out_pattern = "%s/page_%%06d.pdf" % out_dir
    try:
        run_command((PDFTK_PATH, pdf_path, "burst", "output", out_pattern))
    except Exception:
        if cleanOnFail:
            shutil.rmtree(out_dir)
        raise
    out_files = os.listdir(out_dir)
    out_files.sort()
    return [os.path.join(out_dir, filename) for filename in out_files]


def gen_xfdf(datas=None):
    """Generates a temp XFDF file suited for fill_form function, based on dict input data"""
    if datas is None:
        datas = {}
    fields = []
    for key, value in datas.items():
        fields.append(
            """        <field name="%s"><value>%s</value></field>""" % (key, value)
        )
    tpl = """<?xml version="1.0" encoding="UTF-8"?>
<xfdf xmlns="http://ns.adobe.com/xfdf/" xml:space="preserve">
    <fields>
%s
    </fields>
</xfdf>""" % "\n".join(
        fields
    )
    handle, out_file = tempfile.mkstemp()
    f = os.fdopen(handle, "wb")
    f.write(tpl.encode("UTF-8"))
    f.close()
    return out_file


def replace_page(pdf_path, page_number, pdf_to_insert_path):
    """
    Replace a page in a PDF (pdf_path) by the PDF pointed by pdf_to_insert_path.
    page_number is the number of the page in pdf_path to be replaced. It is 1-based.
    """
    A = "A=" + pdf_path
    B = "B=" + pdf_to_insert_path
    output_temp = tempfile.mktemp(suffix=".pdf")

    if page_number == 1:  # At begin
        upper_bound = "A" + str(page_number + 1) + "-end"
        args = (PDFTK_PATH, A, B, "cat", "B", upper_bound, "output", output_temp)
    elif page_number == get_num_pages(pdf_path):  # At end
        lower_bound = "A1-" + str(page_number - 1)
        args = (PDFTK_PATH, A, B, "cat", lower_bound, "B", "output", output_temp)
    else:  # At middle
        lower_bound = "A1-" + str(page_number - 1)
        upper_bound = "A" + str(page_number + 1) + "-end"
        args = (
            PDFTK_PATH,
            A,
            B,
            "cat",
            lower_bound,
            "B",
            upper_bound,
            "output",
            output_temp,
        )

    run_command(args)
    shutil.copy(output_temp, pdf_path)
    os.remove(output_temp)


def stamp(pdf_path, stamp_pdf_path, output_pdf_path=None):
    """
    Applies a stamp (from stamp_pdf_path) to the PDF file in pdf_path. Useful for watermark purposes. # noqa: B950
    If not output_pdf_path is provided, it returns a temporary file with the result PDF.
    """
    output = output_pdf_path or tempfile.mktemp(suffix=".pdf")
    args = [PDFTK_PATH, pdf_path, "multistamp", stamp_pdf_path, "output", output]
    run_command(args)
    return output


def pdftk_cmd_util(pdf_path, action="compress", out_file=None, flatten=True):
    """
    :type action: should valid action, in string format. Eg: "uncompress"
    :param pdf_path: input PDF file
    :param out_file: (default=auto) : output PDF path. will use tempfile if not
    provided
    :param flatten: (default=True) : flatten the final PDF
    :return: name of the output file.
    """
    actions = ["compress", "uncompress"]
    assert action in actions, (
        "Unknown action. Failed to perform given action '%s'." % action
    )

    handle = None
    cleanOnFail = False
    if not out_file:
        cleanOnFail = True
        handle, out_file = tempfile.mkstemp()

    cmd = "%s %s output %s %s" % (PDFTK_PATH, pdf_path, out_file, action)

    if flatten:
        cmd += " flatten"
    try:
        run_command(cmd, True)
    except Exception:
        if cleanOnFail:
            os.remove(out_file)
        raise
    finally:
        if handle:
            os.close(handle)
    return out_file


def compress(pdf_path, out_file=None, flatten=True):
    """
    These are only useful when you want to edit PDF code in a text
    editor like vim or emacs.  Remove PDF page stream compression by
    applying the uncompress filter. Use the compress filter to
    restore compression.

    :param pdf_path: input PDF file
    :param out_file: (default=auto) : output PDF path. will use tempfile if not provided
    :param flatten: (default=True) : flatten the final PDF
    :return: name of the output file.
    """

    return pdftk_cmd_util(pdf_path, "compress", out_file, flatten)


def uncompress(pdf_path, out_file=None, flatten=True):
    """
    These are only useful when you want to edit PDF code in a text
    editor like vim or emacs.  Remove PDF page stream compression by
    applying the uncompress filter. Use the compress filter to
    restore compression.

    :param pdf_path: input PDF file
    :param out_file: (default=auto) : output PDF path. will use tempfile if not provided
    :param flatten: (default=True) : flatten the final PDF
    :return: name of the output file.
    """

    return pdftk_cmd_util(pdf_path, "uncompress", out_file, flatten)
