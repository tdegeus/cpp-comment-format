import unittest

import cpp_comment_format


class Test(unittest.TestCase):
    """ """

    def test_javadoc_doxygen(self):
        """ """

        text = r"""
    /**
    This is a docstring.

    \param a This is a parameter.
    \return This is a return value.
    */
    int foo(int a);
        """

        expected = """
    /**
     * This is a docstring.
     *
     * @param a This is a parameter.
     * @return This is a return value.
     */
    int foo(int a);
        """

        ret = cpp_comment_format.format(text, style="javadoc", doxygen="@")
        self.assertEqual(ret, expected)
        self.assertEqual(cpp_comment_format.format(ret, style="javadoc", doxygen="@"), expected)

    def test_javadoc_doxygen_2(self):
        """ """

        text = r"""
    /**
    This is a docstring.

    @param a This is a parameter.
    @return This is a return value.
    */
    int foo(int a);
        """

        expected = r"""
    /**
     * This is a docstring.
     *
     * \param a This is a parameter.
     * \return This is a return value.
     */
    int foo(int a);
        """

        ret = cpp_comment_format.format(text, style="javadoc", doxygen="\\")
        self.assertEqual(ret, expected)
        self.assertEqual(cpp_comment_format.format(ret, style="javadoc", doxygen="\\"), expected)


if __name__ == "__main__":

    unittest.main(verbosity=2)
