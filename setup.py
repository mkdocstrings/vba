import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mkdocstrings-vba",
    author="Rudolf Byker",
    author_email="rudolfbyker@gmail.com",
    description="MkDocstrings VBA handler",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AutoActuary/mkdocstrings-vba",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    use_scm_version={
        "write_to": "src/version.py",
    },
    setup_requires=[
        "setuptools_scm",
    ],
    install_requires=[
        "mkdocstrings[python]>=0.18",
        "mkdocs-material",
    ],
)
