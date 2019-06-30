import os
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
package_extend = os.path.join(os.getcwd(), 'packages')
sys.path.append(package_extend)
from conf.globals import ORACLE_NLS_LANG
os.environ['NLS_LANG'] = ORACLE_NLS_LANG
from seemmo.common.logging import init
init()