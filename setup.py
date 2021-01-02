from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='IEC61107',
    version='0.1',
    author="Example Author",
    author_email="author@example.com",
    description="Smart meter interface library",
    packages=find_packages(),
    long_description=open(join(dirname(__file__), 'README.md')).read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "pyserial"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
)