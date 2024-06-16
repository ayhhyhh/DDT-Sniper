import os
import importlib.util
import ctypes
import inspect

# 指定目录路径
directory = './script'

def get_script_name():
    if not os.path.exists(directory):
        os.mkdir(directory)
    script_name_list = []
    for filename in os.listdir(directory):
        if filename.endswith('.py'):
            module_name = os.path.splitext(filename)[0]
            script_name_list.append(module_name)
    return script_name_list


def start_script(script_name, handle):
    script_name += '.py'
    module_name = os.path.splitext(script_name)[0]
    module_path = os.path.join(directory, script_name)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type):
            if obj.__name__ == 'ScriptStatus':
                s = obj(handle)
                tid = s.start()
                return tid


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        return False
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
    return True

def stop_script(thread_ident):
    _async_raise(thread_ident, SystemExit)








