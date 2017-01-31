from distutils.core import setup
import py2exe
 
setup(
    options = {'py2exe': {
        'bundle_files': 1
    }},
    console = [{'script': 'gps_server.py',"icon_resources": [(1, "icon.png")]}],
	zipfile = None
)