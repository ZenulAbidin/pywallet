import os
import sys

# -- Path setup --------------------------------------------------------------
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('../zpywallet'))

# -- Project information -----------------------------------------------------
project = 'ZpyWallet'
author = 'Ali Sherief'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Options for HTML output -------------------------------------------------
html_title = 'ZPyWallet Documentation'
#html_logo = '_static/logo.png'
html_theme_options = {
    #'logo_only': True,
    'display_version': False,
}

# -- Extension configuration -------------------------------------------------
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
