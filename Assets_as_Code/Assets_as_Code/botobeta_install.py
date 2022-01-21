import pip

def install_whl(path):
    pip.main(['install', path])

install_whl("/Users/wangzyn/WorkDocs/QS/Beta/Beta-5/SDKs/python-sdk/botocore-1.23.32-py3-none-any.whl")