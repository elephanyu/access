# coding:utf-8
from __future__ import absolute_import

import logging
import traceback
from xml.etree import ElementTree

def xmlParse(string):
    def xmlContentParse(node):
        if len(node.getchildren()) == 0:
            return node.text if node.text is not None else ''
        else:
            node_array = {}
            for child in node.getchildren():
                if child.tag in node_array.keys():
                    if not isinstance(node_array[child.tag], list):
                        node_array[child.tag] = [node_array[child.tag]]
                    node_array[child.tag].append(xmlContentParse(child))
                else:
                    node_array[child.tag] = xmlContentParse(child)
            return node_array
    ret = dict()
    element = ElementTree.fromstring(string)
    try:
        ret[element.tag] = xmlContentParse(element)
        return ret
    except Exception:
        logging.error('parse xml faild, err: %s' % traceback.format_exc())
        return None
