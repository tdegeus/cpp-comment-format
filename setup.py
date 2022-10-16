from pathlib import Path

from setuptools import find_packages
from setuptools import setup

project_name = "cpp_comment_format"

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name=project_name,
    license="MIT",
    author="Tom de Geus",
    author_email="tom@geus.me",
    description="Format comment blocks in C++ source files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="C++",
    url=f"https://github.com/tdegeus/{project_name:s}",
    packages=find_packages(exclude=["tests"]),
    use_scm_version={"write_to": f"{project_name}/_version.py"},
    setup_requires=["setuptools_scm"],
    install_requires=[],
    entry_points={
        "console_scripts": [
            f"cpp_comment_format = {project_name}:_cli",
        ]
    },
)
