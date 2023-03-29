import unittest

import cpp_comment_format


class TestClangFormat(unittest.TestCase):
    """ """

    def test_Docstrings_basic(self):
        code = """
        /**
        * This is the global docstring.
        * @code{.cpp}
        * int a=0;
        * @endcode
        */

        /**
         * My first function.
         * @param a This is a parameter.
         */
        int foo(int a);
        """

        formatted = """
        /**
        * This is the global docstring.
        * @code{.cpp}
        * int a = 0;
        * @endcode
        */

        /**
         * My first function.
         * @param a This is a parameter.
         */
        int foo(int a);
        """

        ret = cpp_comment_format.clang_format(code)
        self.assertEqual(formatted.strip(), ret.strip())


if __name__ == "__main__":
    unittest.main(verbosity=2)
