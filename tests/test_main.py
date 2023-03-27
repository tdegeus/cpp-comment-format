import unittest

import cpp_comment_format


class Test(unittest.TestCase):
    """ """

    def test_Docstrings_basic(self):
        code = """
        /**
        * This is the global docstring.
        */

        /**
         * My first function.
         */
        int foo(int a);
        """.lstrip()

        self.assertEqual(code, str(cpp_comment_format.Docstrings(code)))

        code = """
        /**
        * This is the global docstring.
        */
        #ifndef HEADER_H
        #define HEADER_H

        #define some macro

        /**
         * My first function.
         */
        int foo(int a);

        #endif
        """.lstrip()

        self.assertEqual(code, str(cpp_comment_format.Docstrings(code)))

    def test_Docstrings(self):
        docstrings = [
            """
            /**
             * My first docstring.
             */
            """,
            """
            /**
             * My second docstring.
             * @param a This is a parameter.
             */
            """,
            """
            /**
             * My third docstring.
             * @param a This is a parameter.
             * @return This is a return value.
             */
            """,
        ]

        code = f"""
        {docstrings[0]}
        int foo(int a);

        {docstrings[1]}
        int bar(int a);

        {docstrings[2]}
        int baz(int a);
        """

        docs = cpp_comment_format.Docstrings(code)

        for i, doc in enumerate(docs):
            self.assertEqual(doc.strip(), docstrings[i].strip())

        self.assertEqual(str(docs).strip(), code.strip())
        self.assertEqual(str(docs), str(cpp_comment_format.Docstrings(str(docs))))

    def test_quotes(self):
        code = """
        /**
         * This is a ``docstring``.
         */
        """

        formatted = """
        /**
         * This is a `docstring`.
         */
        """

        self.assertEqual(cpp_comment_format.change_quotes(code, "``", "`"), formatted)

        code = """
        /**
         * This ``is`` a ``docstring``.
         */
        """

        formatted = """
        /**
         * This `is` a `docstring`.
         */
        """

        self.assertEqual(cpp_comment_format.change_quotes(code, "``", "`"), formatted)

    @unittest.skip("Bug")
    def test_quotes_bug(self):
        code = """
        /**
         * This is a docstring.
         * square box with edge-size ``(2 * size + 1) * h``, around ``element``.
         */
        """

        formatted = """
        /**
         * This is a docstring.
         * square box with edge-size `(2 * size + 1) * h`, around `element`.
         */
        """

        self.assertEqual(cpp_comment_format.change_quotes(code, "``", "`"), formatted)

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
     * Global docstring.
     */
    #ifndef HEADER_H
    #define HEADER_H

    /**
    This is a docstring.

    @param a This is a parameter.
    @return This is a return value.
    */
    int foo(int a);

    #endif
        """

        expected = r"""
    /**
     * Global docstring.
     */
    #ifndef HEADER_H
    #define HEADER_H

    /**
     * This is a docstring.
     *
     * \param a This is a parameter.
     * \return This is a return value.
     */
    int foo(int a);

    #endif
        """

        ret = cpp_comment_format.format(text, style="javadoc", doxygen="\\")
        self.assertEqual(ret, expected)
        self.assertEqual(cpp_comment_format.format(ret, style="javadoc", doxygen="\\"), expected)

    def test_javadoc_doxygen_3(self):
        """ """

        text = r"""/**
* This is a docstring.
*
* \param a This is a parameter.
* \return This is a return value.
*/
int foo(int a);
        """

        expected = """/**
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

    def test_javadoc_doxygen_4(self):
        """ """

        text = r"""    /**
    * This is a docstring.
    *
    * \param a This is a parameter.
    * \return This is a return value.
    */
    int foo(int a);
        """

        expected = """    /**
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

    def test_mixed_style(self):
        """ """

        text = r"""
    /**
    This is a docstring.

    \param a This is a parameter.
    \return This is a return value.
    */
    int foo(int a) {
        /* with a comment */
    }
        """

        expected = """
    /**
     * This is a docstring.
     *
     * @param a This is a parameter.
     * @return This is a return value.
     */
    int foo(int a) {
        /* with a comment */
    }
        """

        ret = cpp_comment_format.format(text, style="javadoc", doxygen="@")
        self.assertEqual(ret, expected)
        self.assertEqual(cpp_comment_format.format(ret, style="javadoc", doxygen="@"), expected)

    def test_indentation(self):
        """ """

        text = """
    /**
     * This is a docstring::
     *
     *     int foo(int a);
     *
     * @param a This is a parameter.
     * @return This is a return value.
     */
    int foo(int a);
        """

        expected = """
    /**
     * This is a docstring::
     *
     *      int foo(int a);
     *
     * @param a This is a parameter.
     * @return This is a return value.
     */
    int foo(int a);
        """

        ret = cpp_comment_format.format(text, style="javadoc", doxygen="@", align_codeblock=True)
        self.assertEqual(ret, expected)
        self.assertEqual(cpp_comment_format.format(ret, style="javadoc", doxygen="@"), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
