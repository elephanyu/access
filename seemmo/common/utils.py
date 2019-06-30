from __future__ import absolute_import
__author__ = 'wto'

def getReflectClass(module_path, class_name):
    module_name = class_name[0].lower() + class_name[1:]
    module_file_path = module_path + '.' + module_name
    module_object = __import__(module_file_path, fromlist=True)
    module_class = getattr(module_object, class_name)
    return module_class

def increase(stats, key, threadId):
    sumKey = '%s-%s' % (key, threadId)
    cflagKey = '%s.%s.%s' % (key, threadId, 'cflag')
    if stats.has_key(sumKey):
        if stats[cflagKey]:
            stats[sumKey] = 1
            stats[cflagKey] = False
        else:
            stats[sumKey] += 1
    else:
        stats[sumKey] = 1
        stats[cflagKey] = False

if __name__ == '__main__':
    print getReflectClass('seemmo.procs', 'ReaderProc')