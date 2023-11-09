import os
import os.path as osp

PACKAGE_DIR = osp.dirname(__file__)
PROJECT_DIR = osp.dirname(PACKAGE_DIR)

STATIC_DIR = os.environ.get('TIS_STATIC_DIR',None) or osp.join(PACKAGE_DIR,"static")
OUTPUT_DIR = os.environ.get('TIS_OUTPUT_DIR',None) or osp.join(PROJECT_DIR,"output")
