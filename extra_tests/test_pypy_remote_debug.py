import os
import sys
import pytest
import subprocess

try:
    import __pypy__
except ImportError:
    pytest.skip('can only run these tests on pypy')

if not sys.platform.startswith('linux'):
    pytest.skip('only works on linux so far')

import _pypy_remote_debug
import _vmprof

def test_parse_maps():
    maps = _pypy_remote_debug._parse_maps('self', sys.executable)
    assert os.path.realpath(sys.executable) == maps[0]['file']

def test_elf_find_symbol():
    pid = os.getpid()
    file, base_addr = _pypy_remote_debug._find_file_and_base_addr(pid)
    with open(file, 'rb') as f:
        value = _pypy_remote_debug.elf_find_symbol(f, b'pypysig_counter')
    # compare against output of nm
    out = subprocess.check_output(['nm', file])
    if not out:
        pytest.skip("test can't work on stripped binary")
    for line in out.splitlines():
        if 'pypysig_counter' in line:
            addr, _, _ = line.split()
            assert int(addr, 16) == value
            break
    else:
        assert False
    assert value

def test_elf_read_first_load_section():
    pid = os.getpid()
    file, base_addr = _pypy_remote_debug._find_file_and_base_addr(pid)
    with open(file, 'rb') as f:
        phdr = _pypy_remote_debug.elf_read_first_load_section(f)

    # compare against output of objdump
    out = subprocess.check_output(['objdump', '-p', file])
    for line in out.splitlines():
        if 'LOAD' in line:
            outline = line
            break
    content = outline.split()[1:]
    for name, value in zip(content[::2], content[1::2]):
        if name == 'vaddr':
            assert int(value, 16) == phdr.vaddr

def test_read_memory():
    # test using local memory
    ffi = _pypy_remote_debug.ffi
    pid = os.getpid()
    data = b'hello, world!'
    sourcebuffer = ffi.new('char[]', len(data))
    for i in range(len(data)):
        sourcebuffer[i] = data[i:i+1]
    result = _pypy_remote_debug.read_memory(pid, int(ffi.cast('intptr_t', sourcebuffer)), len(data))
    assert result == data

def test_write_memory():
    # test using local memory
    ffi = _pypy_remote_debug.ffi
    pid = os.getpid()
    data = b'hello, world!'
    targetbuffer = ffi.new('char[]', len(data))
    result = _pypy_remote_debug.write_memory(pid, int(ffi.cast('intptr_t', targetbuffer)), data)
    assert ffi.buffer(targetbuffer)[:] == data

def test_cookie():
    pid = os.getpid()
    addr = _pypy_remote_debug.compute_remote_addr(pid)
    cookie = _pypy_remote_debug.read_memory(pid, addr + _pypy_remote_debug.COOKIE_OFFSET, 8)
    assert cookie == b'pypysigs'

def test_remote_find_file_and_base_addr():
    code = """
import sys
sys.stdin.readline()
"""
    out = subprocess.Popen([sys.executable, '-c',
         code], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    pid = out.pid
    file, base_addr = _pypy_remote_debug._find_file_and_base_addr(pid)
    assert file == sys.executable or 'libpypy' in file
    out.stdin.write(b'1\n')
    out.stdin.flush()
    out.wait()

def test_integration():
    import __pypy__
    for func in (_pypy_remote_debug.start_debugger, __pypy__.remote_exec):
        code = """
import time
for i in range(20):
    time.sleep(0.1)
"""
        debug_code = r"""
import sys, os
sys.stdout.write('hello from %s\n' % os.getpid())
sys.stdout.flush()
"""
        out = subprocess.Popen([sys.executable, '-c',
             code], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        pid = out.pid
        func(pid, debug_code)
        l = [out.stdout.readline() for _ in range(len(debug_code.splitlines()) + 2)]
        assert ''.join(l) == 'Executing remote debugger script:\n%s\n' % debug_code
        l = out.stdout.readline()
        assert l == 'hello from %s\n' % pid
        exitcode = out.wait()
        assert exitcode == 0

def test_proc_maps_find_map():
    import ctypes
    pid = os.getpid()
    so = ctypes.CDLL('libexpat.so')
    address_of_function = (ctypes.cast(so.XML_Parse, ctypes.c_void_p)).value
    map = _pypy_remote_debug._proc_maps_find_map(address_of_function)
    assert 'libexpat.so' in map['file']
    assert map['from_'] <= address_of_function < map['to_']
    assert map['base_map']

def test_symbolify():
    import ctypes
    pid = os.getpid()
    so = ctypes.CDLL('libexpat.so')
    address_of_function = (ctypes.cast(so.XML_Parse, ctypes.c_void_p)).value
    name, filename = _pypy_remote_debug._symbolify(address_of_function)
    assert name == b'XML_Parse'
    assert 'libexpat.so' in filename

def test_symbolify_all():
    import ctypes
    pid = os.getpid()
    so = ctypes.CDLL('libexpat.so')
    names = ['XML_Parse', 'XML_GetBase']
    all = []
    for name in names:
        address_of_function = (ctypes.cast(getattr(so, name), ctypes.c_void_p)).value
        all.append(address_of_function)
    all.append(1)
    res = _pypy_remote_debug._symbolify_all(all)
    for index, name in enumerate(names):
        addr = all[index]
        assert res[addr][0] == name.encode('ascii')
        assert 'libexpat.so' in res[addr][1]

def test_symbolify_pypy_function():
    addr = _pypy_remote_debug.compute_remote_addr()
    name, filename = _pypy_remote_debug._symbolify(addr)
    assert name == b'pypysig_counter'
    addr = _pypy_remote_debug.compute_remote_addr(symbolname=b'pypy_g_DiskFile_read')
    name, filename = _pypy_remote_debug._symbolify(addr)
    assert name == b'pypy_g_DiskFile_read'

def test_symbolify_all_pypy_function():
    names = [b'pypy_g_DiskFile_read', b'pypy_g_DiskFile_write']
    all = []
    for name in names:
        address_of_function = _pypy_remote_debug.compute_remote_addr('self', name)
        all.append(address_of_function)
    all.append(1)
    res = _pypy_remote_debug._symbolify_all(all)
    for index, name in enumerate(names):
        addr = all[index]
        assert res[addr][0] == name

@pytest.mark.skipif(not hasattr(_vmprof, 'resolve_addr'), reason="not implemented")
def test_symbolify_vmprof():
    import _vmprof, ctypes
    so = ctypes.CDLL('libexpat.so')
    address_of_function = (ctypes.cast(so.XML_Parse, ctypes.c_void_p)).value
    name, lineno, filename = _vmprof.resolve_addr(address_of_function)
    assert name == 'XML_Parse'
    assert 'libexpat.so' in filename

    result = _vmprof.resolve_addr(1)
    assert result is None

@pytest.mark.skipif(not hasattr(_vmprof, 'resolve_many_addrs'), reason="not implemented")
def test_symbolify_vmprof_many():
    import _vmprof, ctypes
    names = [b'pypy_g_DiskFile_read', b'pypy_g_DiskFile_write']
    all = []
    for name in names:
        address_of_function = _pypy_remote_debug.compute_remote_addr('self', name)
        all.append(address_of_function)

    names2 = ['XML_Parse', 'XML_GetBase']
    so = ctypes.CDLL('libexpat.so')
    for name in names2:
        address_of_function = (ctypes.cast(getattr(so, name), ctypes.c_void_p)).value
        all.append(address_of_function)
    all.append(1)

    res = _vmprof.resolve_many_addrs(all)
    for index, name in enumerate(names + names2):
        addr = all[index]
        assert res[addr][0] == name
