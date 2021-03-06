
import unittest
from conans.client.loader import ConanFileTextLoader,\
    ConanFileLoader
from conans.errors import ConanException
from conans.util.files import save
import os
from conans.model.requires import Requirements
from conans.model.options import OptionsValues
from mock import Mock
from conans.model.settings import Settings
from conans.test.utils.test_files import temp_folder


class ConanLoaderTest(unittest.TestCase):

    def plain_text_parser_test(self):
        # Valid content
        file_content = '''[requires]
OpenCV/2.4.10@phil/stable # My requirement for CV
OpenCV2/2.4.10@phil/stable #
OpenCV3/2.4.10@phil/stable
[generators]
one # My generator for this
two
[options]
OpenCV:use_python=True # Some option
OpenCV:other_option=False
OpenCV2:use_python2=1
OpenCV2:other_option=Cosa #
'''
        parser = ConanFileTextLoader(file_content)
        exp = ['OpenCV/2.4.10@phil/stable',
               'OpenCV2/2.4.10@phil/stable',
               'OpenCV3/2.4.10@phil/stable']
        self.assertEquals(parser.requirements, exp)

    def load_conan_txt_test(self):
        file_content = '''[requires]
OpenCV/2.4.10@phil/stable
OpenCV2/2.4.10@phil/stable
[generators]
one
two
[imports]
OpenCV/bin, * -> ./bin # I need this binaries
OpenCV/lib, * -> ./lib
[options]
OpenCV:use_python=True
OpenCV:other_option=False
OpenCV2:use_python2=1
OpenCV2:other_option=Cosa
'''
        tmp_dir = temp_folder()
        file_path = os.path.join(tmp_dir, "file.txt")
        save(file_path, file_content)
        loader = ConanFileLoader(None, Settings(), OptionsValues.loads(""))
        ret = loader.load_conan_txt(file_path, None)
        options1 = OptionsValues.loads("""OpenCV:use_python=True
OpenCV:other_option=False
OpenCV2:use_python2=1
OpenCV2:other_option=Cosa""")
        requirements = Requirements()
        requirements.add("OpenCV/2.4.10@phil/stable")
        requirements.add("OpenCV2/2.4.10@phil/stable")

        self.assertEquals(ret.requires, requirements)
        self.assertEquals(ret.generators, ["one", "two"])
        self.assertEquals(ret.options.values.dumps(), options1.dumps())

        ret.copy = Mock()
        ret.imports()

        self.assertTrue(ret.copy.call_args_list, [('*', './bin', 'OpenCV/bin'),
                                                  ('*', './lib', 'OpenCV/lib')])

        # Now something that fails
        file_content = '''[requires]
OpenCV/2.4.104phil/stable <- use_python:True, other_option:False
'''
        tmp_dir = temp_folder()
        file_path = os.path.join(tmp_dir, "file.txt")
        save(file_path, file_content)
        loader = ConanFileLoader(None, Settings(), OptionsValues.loads(""))
        with self.assertRaisesRegexp(ConanException, "Wrong package recipe reference(.*)"):
            loader.load_conan_txt(file_path, None)

        file_content = '''[requires]
OpenCV/2.4.10@phil/stable <- use_python:True, other_option:False
[imports]
OpenCV/bin/* - ./bin
'''
        tmp_dir = temp_folder()
        file_path = os.path.join(tmp_dir, "file.txt")
        save(file_path, file_content)
        loader = ConanFileLoader(None, Settings(), OptionsValues.loads(""))
        with self.assertRaisesRegexp(ConanException, "is too long. Valid names must contain"):
            loader.load_conan_txt(file_path, None)
