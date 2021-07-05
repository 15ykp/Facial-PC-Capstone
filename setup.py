import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="FacialPC", # Replace with your own username
    version="0.0.2",
    author="Brandon Caron, Chris Gritter, Alan Pan",
    author_email="14bjc5@queensu.ca",
    description="Program to control PC with only facial expression and movement.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)