from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import os.path as path
import os

CCDC_source_dir = os.path.abspath(os.path.dirname('__file__'))

sccd_extension = Extension(
    name = "pysccd",
    sources = ["pysccd.pyx"],
    libraries = ["sccd"],
    library_dirs = [CCDC_source_dir]
)

setup(
    name = "pysccd",
    ext_modules = cythonize([sccd_extension]),
    author = "Su Ye"
)

