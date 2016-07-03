from setuptools import setup, find_packages

project_url = 'https://github.com/bavovanachte/sphinx-wavedrom'

requires = ['Sphinx>=0.6']

setup(
    name='sphinxcontrib-wavedrom',
    version='1.0.1',
    url='https://github.com/bavovanachte/sphinx-wavedrom',
    download_url='https://github.com/bavovanachte/sphinx-wavedrom/tarball/1.0.1',
    license='MIT license',
    author='Bavo Van Achte',
    author_email='bavo.van.achte@gmail.com',
    description='A sphinx extension that allows generating wavedrom diagrams based on their textual representation',
    long_description=open("README.rst").read(),
    zip_safe=False,
    classifiers=[],
    platforms='any',
    packages=find_packages(exclude=['example']),
    include_package_data=True,
    install_requires=requires,
    namespace_packages=['sphinxcontrib'],
    keywords = ['sphinx', 'wavedrom', 'documentation'],
)