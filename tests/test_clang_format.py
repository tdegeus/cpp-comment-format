import cpp_comment_format


def test_Docstrings_basic():
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
    assert formatted.strip() == ret.strip()
