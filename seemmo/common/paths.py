import os

home_path = os.path.expanduser('~')
script_path = os.getcwd()

def logging_path(module):
    log_path = os.path.join(home_path, 'logs', module)
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    return log_path
