'''
WSGI connector for the proxy app
'''
import sys
import os

app_home = os.path.dirname(os.path.abspath(sys.argv[0]))
virtual_env = os.path.join(app_home, 'venv')
#config_path = os.path.join(app_home, 'config.ini')

sys.path.insert(0, app_home)
import d1_examples

activate_this = os.path.join(virtual_env, 'activate_this.py')
#with open(activate_this) as file_:
#  exec(file_.read(), dict(__file__=activate_this))

application = d1_examples.create_app()