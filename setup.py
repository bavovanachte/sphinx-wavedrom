from setuptools import setup, find_packages

project_url = 'https://github.com/bavovanachte/sphinx-wavedrom'

requires = ['Sphinx>=1.8',
            'wavedrom>=1.9.0rc1',
            'cairosvg>=2;python_version>="3.3"',
            'xcffib;python_version>="3.3"']

setup(
    name='sphinxcontrib-wavedrom',
    use_scm_version={
        "relative_to": __file__,
        "write_to": "sphinxcontrib/version.py",
    },
    url='https://github.com/bavovanachte/sphinx-wavedrom',
    license='MIT license',
    author='Bavo Van Achte, Stefan Wallentowitz',
    author_email='bavo.van.achte@gmail.com, stefan@wallentowitz.de',
    description='A sphinx extension that allows generating wavedrom diagrams based on their textual representation',
    long_description=open("README.rst").read(),
    zip_safe=False,
    classifiers=['Framework :: Sphinx :: Extension'],
    platforms='any',
    packages=find_packages(exclude=['example']),
    include_package_data=True,
    install_requires=requires,
    setup_requires=[
        'setuptools_scm',
    ],
    namespace_packages=['sphinxcontrib'],
    keywords = ['sphinx', 'wavedrom', 'documentation'],
)
