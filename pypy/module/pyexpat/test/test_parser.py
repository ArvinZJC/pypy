from pypy.module.pyexpat.interp_pyexpat import global_storage
from pytest import skip

class AppTestPyexpat:
    spaceconfig = dict(usemodules=['pyexpat', '_multibytecodec'])

    def teardown_class(cls):
        global_storage.clear()

    def test_simple(self):
        import pyexpat
        p = pyexpat.ParserCreate()
        res = p.Parse("<xml></xml>")
        assert res == 1

        exc = raises(pyexpat.ExpatError, p.Parse, "3")
        assert exc.value.lineno == 1
        assert exc.value.offset == 11
        assert exc.value.code == 9 # XML_ERROR_JUNK_AFTER_DOC_ELEMENT

        pyexpat.ExpatError("error")

    def test_attributes(self):
        import pyexpat
        p = pyexpat.ParserCreate()
        def test_setget(p, attr, default=False):
            assert getattr(p, attr) is default
            for x in 0, 1, 2, 0:
                setattr(p, attr, x)
                assert getattr(p, attr) is bool(x), attr
        for attr in ('buffer_text', 'namespace_prefixes', 'ordered_attributes',
                     'specified_attributes'):
            test_setget(p, attr)
        test_setget(p, 'returns_unicode', True)

    def test_version(self):
        import pyexpat
        assert isinstance(pyexpat.__version__, str)
        assert pyexpat.EXPAT_VERSION.startswith('expat_')
        assert isinstance(pyexpat.version_info, tuple)
        assert isinstance(pyexpat.version_info[0], int)

    def test_malformed_xml(self):
        import sys
        if sys.platform == "darwin":
            skip("Fails with the version of expat on Mac OS 10.6.6")
        import pyexpat
        xml = "\0\r\n"
        parser = pyexpat.ParserCreate()
        exc = raises(pyexpat.ExpatError, "parser.Parse(xml, True)")
        assert 'unclosed token: line 2, column 0' in exc.value[0]

    def test_encoding_argument(self):
        import pyexpat
        for encoding_arg in (None, 'utf-8', 'iso-8859-1'):
            for namespace_arg in (None, '{'):
                print(encoding_arg, namespace_arg)
                p = pyexpat.ParserCreate(encoding_arg, namespace_arg)
                data = []
                p.CharacterDataHandler = lambda s: data.append(s)
                encoding = encoding_arg is None and 'utf-8' or encoding_arg

                res = p.Parse(u"<xml>\u00f6</xml>".encode(encoding), True)
                assert res == 1
                assert data == [u"\u00f6"]

    def test_get_handler(self):
        import pyexpat
        p = pyexpat.ParserCreate()
        assert p.StartElementHandler is None
        assert p.EndElementHandler is None
        def f(*args): pass
        p.StartElementHandler = f
        assert p.StartElementHandler is f
        def g(*args): pass
        p.EndElementHandler = g
        assert p.StartElementHandler is f
        assert p.EndElementHandler is g

    def test_intern(self):
        import pyexpat
        p = pyexpat.ParserCreate()
        def f(*args): pass
        p.StartElementHandler = f
        p.EndElementHandler = f
        p.Parse("<xml></xml>")
        assert len(p.intern) == 1

    def test_set_buffersize(self):
        import pyexpat, sys
        p = pyexpat.ParserCreate()
        p.buffer_size = 150
        assert p.buffer_size == 150
        raises(TypeError, setattr, p, 'buffer_size', sys.maxint + 1)

    def test_encoding_xml(self):
        # use one of the few encodings built-in in expat
        xml = "<?xml version='1.0' encoding='iso-8859-1'?><s>caf\xe9</s>"
        import pyexpat
        p = pyexpat.ParserCreate()
        def gotText(text):
            assert text == u"caf\xe9"
        p.CharacterDataHandler = gotText
        assert p.returns_unicode
        p.Parse(xml)

    def test_explicit_encoding(self):
        xml = "<?xml version='1.0'?><s>caf\xe9</s>"
        import pyexpat
        p = pyexpat.ParserCreate(encoding='iso-8859-1')
        def gotText(text):
            assert text == u"caf\xe9"
        p.CharacterDataHandler = gotText
        p.Parse(xml)

    def test_python_encoding(self):
        # This name is not knonwn by expat
        xml = "<?xml version='1.0' encoding='latin1'?><s>caf\xe9</s>"
        import pyexpat
        p = pyexpat.ParserCreate()
        def gotText(text):
            assert text == u"caf\xe9"
        p.CharacterDataHandler = gotText
        p.Parse(xml)

    def test_mbcs(self):
        xml = "<?xml version='1.0' encoding='gbk'?><p/>"
        import pyexpat
        p = pyexpat.ParserCreate()
        exc = raises(ValueError, p.Parse, xml)
        assert str(exc.value) == "multi-byte encodings are not supported"

    def test_invalid_error(self):
        xml = '<fran\xe7ais>Comment \xe7a va ? Tr\xe8s bien ?</fran\xe7ais>'
        import pyexpat
        p = pyexpat.ParserCreate()
        def f(*args): pass
        p.StartElementHandler = f
        exc = raises((UnicodeDecodeError, pyexpat.ExpatError), p.Parse, xml)
        if isinstance(exc.value, UnicodeDecodeError):
            assert exc.value.start == 4
        else:
            assert exc.value.offset == 5
            assert exc.value.lineno == 1

    def test_external_entity(self):
        xml = ('<!DOCTYPE doc [\n'
               '  <!ENTITY test SYSTEM "whatever">\n'
               ']>\n'
               '<doc>&test;</doc>')
        import pyexpat
        p = pyexpat.ParserCreate()
        def handler(*args):
            # context, base, systemId, publicId
            assert args == ('test', None, 'whatever', None)
            return True
        p.ExternalEntityRefHandler = handler
        p.Parse(xml)

    def test_errors(self):
        import types
        import pyexpat
        assert isinstance(pyexpat.errors, types.ModuleType)
        # check a few random errors
        assert pyexpat.errors.XML_ERROR_SYNTAX == 'syntax error'
        assert (pyexpat.errors.XML_ERROR_INCORRECT_ENCODING ==
               'encoding specified in XML declaration is incorrect')
        assert (pyexpat.errors.XML_ERROR_XML_DECL ==
                'XML declaration not well-formed')

    def test_model(self):
        import pyexpat
        assert isinstance(pyexpat.model.XML_CTYPE_EMPTY, int)

    def test_read_chunks(self):
        import pyexpat
        import StringIO
        from contextlib import closing

        xml = '<xml>' + (' ' * 4096) + '</xml>'
        with closing(StringIO.StringIO(xml)) as sio:
            class FakeReader():
                def __init__(self):
                    self.read_count = 0

                def read(self, size):
                    self.read_count += 1
                    assert size > 0
                    return sio.read(size)

            fake_reader = FakeReader()
            p = pyexpat.ParserCreate()
            p.ParseFile(fake_reader)
            assert fake_reader.read_count == 4

    def test_entities(self):
        import pyexpat
        parser = pyexpat.ParserCreate(None, "")

        def startElement(tag, attrs):
            assert tag == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#RDF'
            assert attrs == {
                'http://www.w3.org/XML/1998/namespacebase':
                'http://www.semanticweb.org/jiba/ontologies/2017/0/test'}
        parser.StartElementHandler = startElement
        parser.Parse("""<?xml version="1.0"?>

        <!DOCTYPE rdf:RDF [
        <!ENTITY owl "http://www.w3.org/2002/07/owl#" >
        <!ENTITY xsd "http://www.w3.org/2001/XMLSchema#" >
        <!ENTITY rdfs "http://www.w3.org/2000/01/rdf-schema#" >
        <!ENTITY rdf "http://www.w3.org/1999/02/22-rdf-syntax-ns#" >
        ]>

        <rdf:RDF xmlns="http://www.semanticweb.org/jiba/ontologies/2017/0/test#"
          xml:base="http://www.semanticweb.org/jiba/ontologies/2017/0/test"
          xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
          xmlns:owl="http://www.w3.org/2002/07/owl#"
          xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
          xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        </rdf:RDF>
        """, True)

class AppTestPyexpat2:
    spaceconfig = dict(usemodules=['pyexpat', 'itertools', '_socket',
                                   'time', 'struct', 'binascii'])

    def setup_class(cls):
        import py, sys
        if sys.platform != 'linux2':
            py.test.skip("even if we add all the crazy includes to run ctypes, it ends with MallocMismatch")

    def test_django_bug(self):
        xml_str = '<?xml version="1.0" standalone="no"?><!DOCTYPE example SYSTEM "http://example.com/example.dtd"><root/>'

        from xml.dom import pulldom
        from xml.sax import handler
        from xml.sax.expatreader import ExpatParser as _ExpatParser
        from StringIO import StringIO

        class DefusedExpatParser(_ExpatParser):
            def start_doctype_decl(self, name, sysid, pubid, has_internal_subset):
                raise DTDForbidden(name, sysid, pubid)

            def external_entity_ref_handler(self, context, base, sysid, pubid):
                raise ExternalReferenceForbidden(context, base, sysid, pubid)

            def reset(self):
                _ExpatParser.reset(self)
                parser = self._parser
                parser.StartDoctypeDeclHandler = self.start_doctype_decl
                parser.ExternalEntityRefHandler = self.external_entity_ref_handler


        class DTDForbidden(ValueError):
            pass


        class ExternalReferenceForbidden(ValueError):
            pass

        stream = pulldom.parse(StringIO(xml_str), DefusedExpatParser())

        try:
            for event, node in stream:
                print(event, node)
        except DTDForbidden:
            pass
        else:
            raise Exception("should raise DTDForbidden")

    def test_ErrorString_crash(self):
        import pyexpat
        assert pyexpat.ErrorString(-1) is None
