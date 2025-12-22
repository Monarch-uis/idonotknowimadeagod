# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------
project = 'EPUB to Audiobook/Video Converter'
copyright = '2024, Your Name'
author = 'Your Name'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',        # Auto-generate docs from docstrings
    'sphinx.ext.napoleon',       # Support for Google/NumPy docstring styles
    'sphinx.ext.viewcode',       # Add links to source code
    'sphinx.ext.intersphinx',    # Link to other project docs
    'sphinx.ext.todo',           # Support for TODO items
    'sphinx.ext.coverage',       # Coverage checking
    'sphinx.ext.autosummary',    # Generate summary tables
    'sphinx_rtd_theme',          # Read the Docs theme
    'myst_parser',               # Markdown support
]

# Autosummary settings
autosummary_generate = True
autosummary_imported_members = False

# Napoleon settings (for Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The suffix(es) of source filenames.
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# The master toctree document.
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'canonical_url': '',
    'analytics_id': '',
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
    # Toc options
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# Add any paths that contain custom static files (such as style sheets)
html_static_path = ['_static']

# Custom sidebar templates
html_sidebars = {
    '**': [
        'globaltoc.html',
        'relations.html',
        'sourcelink.html',
        'searchbox.html',
    ]
}

# -- Options for HTMLHelp output ---------------------------------------------
htmlhelp_basename = 'EPUBConverterdoc'

# -- Options for LaTeX output ------------------------------------------------
latex_elements = {}
latex_documents = [
    (master_doc, 'EPUBConverter.tex', 'EPUB Converter Documentation',
     'Author', 'manual'),
]

# -- Options for manual page output ------------------------------------------
man_pages = [
    (master_doc, 'epubconverter', 'EPUB Converter Documentation',
     [author], 1)
]

# -- Options for Texinfo output ----------------------------------------------
texinfo_documents = [
    (master_doc, 'EPUBConverter', 'EPUB Converter Documentation',
     author, 'EPUBConverter', 'Convert EPUB files to audiobooks and videos.',
     'Miscellaneous'),
]

# -- Extension configuration -------------------------------------------------

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'moviepy': ('https://zulko.github.io/moviepy/', None),
}

# Todo extension
todo_include_todos = True

# Coverage extension
coverage_show_missing_items = True
