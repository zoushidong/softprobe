from PyInstaller.hooks.hookutils import (collect_data_files, collect_submodules)

datas = [('/usr/local/lib/python2.7/dist-packages/psutil/_psutil_linux.so', 'psutil'),
         ('/usr/local/lib/python2.7/dist-packages/psutil/_psutil_posix.so', 'psutil')]
hiddenimports = collect_submodules('psutil')