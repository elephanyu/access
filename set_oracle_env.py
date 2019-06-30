# coding: utf-8
import os
import commands

if __name__ == '__main__':
    code_path = os.path.dirname(os.path.realpath(__file__))
    lib_path = os.path.join(code_path, 'lib')
    if not os.path.exists(lib_path):
        print("Data inner application is not in oracle method, so it need not to set os['LD_LIBRARY_PATH']")
    file_path = os.path.expanduser('~') + '/.bashrc'
    grep_cmd = 'egrep LD_LIBRARY_PATH %s' % file_path
    grep_status, grep_ret = commands.getstatusoutput(grep_cmd)
    if grep_ret:
        if file_path not in os.environ['LD_LIBRARY_PATH']:
            add_cmd = "echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:%s' >>%s" % (lib_path, file_path)
            add_status, add_ret = commands.getstatusoutput(add_cmd)
            if add_status == 0:
                print '%s add to LD_LIBRARY_PATH' % lib_path
                print "please run 'source %s' in bash shell" % file_path
            else:
                print add_ret
        else:
            print "%s has in os['LD_LIBRARY_PATH']"
    else:
        add_cmd = "echo 'export LD_LIBRARY_PATH=%s' >>%s" % (lib_path, file_path)
        add_status, add_ret = commands.getstatusoutput(add_cmd)
        if add_status == 0:
            print '%s add to LD_LIBRARY_PATH' % lib_path
            print "please run 'source %s' in bash shell" % file_path
        else:
            print add_ret
