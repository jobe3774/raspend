import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="raspend",
    version="0.0.1",
    author="Joerg Beckers",
    author_email="pypi@jobe-software.de",
    description="An easy to use and small HTTP backend framework for the Raspberry Pi",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jobe3774/raspend.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)