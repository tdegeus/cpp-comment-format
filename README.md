# cpp_comment_format

Format code blocks.

## From command line

Default style, print result to screen:
```bash
cpp_comment_format example.cpp
```

To modify in place:
```bash
cpp_comment_format -i example.cpp
```

Using a specific style:
```bash
cpp_comment_format --style "javadoc" --doxygen "@" example.cpp
```

## Using pre-commit

Default style:
```yaml
repos:
- repo: https://github.com/tdegeus/cpp_comment_format
  rev: v0.0.2
  hooks:
  - id: cpp_comment_format
```

Using a specific style:
```yaml
repos:
- repo: https://github.com/tdegeus/cpp_comment_format
  rev: v0.0.2
  hooks:
  - id: cpp_comment_format
    args: ["--style", "javadoc", "--doxygen", "@"]
```
