################################################################################
refac
################################################################################




The project setup is documented in `a separate document <project_setup.rst>`_. Feel free to remove this document (and/or the link to this document) if you don't need it.

Installation
------------

To install refac, do:

.. code-block:: console

  git clone https://github.com//refac.git
  cd refac
  pip install .


Run tests (including coverage) with:

.. code-block:: console

  python setup.py test

Usage
*************
To remove implicit real statements:

.. code-block:: console
python ~/refac/refac/clean_use_and_implicit.py --clean_implicit src/dmc/mc_configs.f

To clean variables in use statements:

python ~/refac/refac/clean_use_and_implicit.py --clean_use src/dmc/mc_configs.f

Documentation
*************

.. _README:

Include a link to your project's full documentation here.

Contributing
************

If you want to contribute to the development of refac,
have a look at the `contribution guidelines <CONTRIBUTING.rst>`_.

License
*******

Copyright (c) 2020, Netherlands eScience Center

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.



Credits
*******

This package was created with `Cookiecutter <https://github.com/audreyr/cookiecutter>`_ and the `NLeSC/python-template <https://github.com/NLeSC/python-template>`_.
