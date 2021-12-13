#!/usr/bin/env python

"""
Pandoc filter to process code blocks with class "plantuml" into
plant-generated images.
Needs `plantuml.jar` from http://plantuml.com/.
"""

import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.DEBUG)

from pandocfilters import toJSONFilter, Para, Image
from pandocfilters import get_filename4code, get_caption, get_extension

JAVA_BIN = os.environ.get('JAVA_BIN', 'java')
PLANTUML_JAR = os.environ.get('PLANTUML_BIN', os.path.expanduser('~/.local/bin/plantuml.jar'))
PLANTUML_OPTS = os.environ.get('PLANTUML_OPTS', '-charset utf-8')
PLANTUML_OPTS = PLANTUML_OPTS.split(' ')


def rel_mkdir_symlink(src, dest):
    dest_dir = os.path.dirname(dest)
    if dest_dir and not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    if os.path.exists(dest):
        os.remove(dest)

    src = os.path.relpath(src, dest_dir)
    os.symlink(src, dest)


def plantuml(key, value, format_, _):
    if key == 'CodeBlock':
        [[ident, classes, keyvals], code] = value

        if "plantuml" in classes:
            caption, typef, keyvals = get_caption(keyvals)

            filename = get_filename4code("plantuml", code)
            filetype = get_extension(format_, "svg", html="svg", latex="svg")

            src = filename + '.uml'
            dest = filename + '.' + filetype

            # Generate image only once
            if not os.path.isfile(dest):
                txt = code.encode(sys.getfilesystemencoding())
                if not txt.startswith(b"@start"):
                    txt = b"@startuml\n" + txt + b"\n@enduml\n"
                with open(src, "wb") as f:
                    f.write(txt)

                params = [
                    JAVA_BIN,
                    '-jar',
                    PLANTUML_JAR
                ] + PLANTUML_OPTS
                params = params + [f'-t{filetype}', src]
                logging.debug(params)
                subprocess.check_call(params)
                logging.info('Created image ' + dest + '\n')

            # Update symlink each run
            for ind, keyval in enumerate(keyvals):
                if keyval[0] == 'plantuml-filename':
                    link = keyval[1]
                    keyvals.pop(ind)
                    rel_mkdir_symlink(dest, link)
                    dest = link
                    break

            return Para([Image([ident, [], keyvals], caption, [dest, typef])])


def main():
    toJSONFilter(plantuml)


if __name__ == "__main__":
    main()
