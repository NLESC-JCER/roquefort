################################################################################
Roquefort
################################################################################


A tool for **R**efactoring **O**f **QUE**stionable **FORT**ran 

There are three possible actions --action {clean_common, clean_use, clean_implicit}

+ clean_common: Delete common a block, add the correspoinding block as a module in file m_common.f90.

+ clean_use: Delete unused variables imported by 'use' statements.

+ clean_implicit: Replace 'implicit real' by implicit none and declare variables using regular explicit declaration. 

Subflags of --action options are:

+ --action clean_common --common_block_name, -n /string/ --path_to_source, -p /string/
+ --action clean_use (or clean_implicit) --filename /string/ --overwrite, -ow

The project setup is documented in `a separate document <project_setup.rst>`_. Feel free to remove this document (and/or the link to this document) if you don't need it.

Installation
------------

To install roquefort, do:

.. code-block:: console

  git clone https://github.com//roquefort.git
  cd roquefort
  pip install .


Run tests (including coverage) with:

.. code-block:: console

  python setup.py test

Usage
-----------------------

Remove Common block
***********************

Common blocks are not unusual to find in Fortran77 code. It recommended to move this common block to modules. 
The original Fortran code is :

.. code-block:: fortran 


  subroutine func()

  common /mod1/ var1, var2
  common /mod2/ var3, var4

  implicit real*8(a-h,o-z)

  x = var1
  y = var2

  i = 2

  end

To remove common blocks: 

.. code-block:: console

  python roquefort_fortran.py --action clean_common -n mod1 -p ./example/

Clean unused imported variable
*********************************

To clean variables in use statements:

.. code-block:: console

  python roquefort_fortran.py --action clean_use --filename regterg.f90

To remove implicit real statements:

.. code-block:: console

  python roquefort_fortran.py --action clean_implicit --filename splfit.f -ow

Documentation
*************

.. _README:

Include a link to your project's full documentation here.

Contributing
************

If you want to contribute to the development of roquefort,
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
