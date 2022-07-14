################################################################################
Roquefort
################################################################################
A tool for **R**\ efactoring **O**\ f **QUE**\ stionable **FORT**\ ran 

Features
-------------

Roquefort allows to :

- `Automatically create module to replace existing common blocks <https://github.com/NLESC-JCER/roquefort#remove-common-block>`_.
- `Clean unused variable imported from modules <https://github.com/NLESC-JCER/roquefort#clean-unused-imported-variable>`_.
- `Automatically transform implicit variable declaration to explicit variable declaration  <https://github.com/NLESC-JCER/roquefort/blob/master/README.rst#remove-implicit-variable>`_.
- `Move variable to new module <https://github.com/NLESC-JCER/roquefort/blob/master/README.rst#move-variable-in-new-module>`_.


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

  python refac_fortran.py --action clean_common -n mod1 -p ./example/

Leads to the code :

.. code-block:: fortran

      subroutine func()


      use mod1, only: var1, var2
      implicit real*8(a-h,o-z)


      common /mod2/ var3, var4
      

      x = var1
      y = var2

      i = 2
      
      end

with the additional module file 

.. code-block:: fortran

 module mod1
   !> Arguments: var1, var2
   use precision_kinds, only: dp
   include 'vmc.h'

    real(dp) :: var1
    real(dp) :: var2
    private

    public :: var1, var2
    save
 end module mod1

Clean unused imported variable
*********************************

Unused varialbe can pollute use statements. For example in the code

.. code-block:: fortran

      subroutine func()

      use mod1, only: var1, var2
      use mod2, only: var3

      implicit none

      integer :: i, j

      i = var1
      j = var3

      end

The variable `var2` of `mod1` is not used. We can remove that variable with


.. code-block:: console

  python refac_fortran.py --action clean_use --filename ../example/test_use.f


Leading to 

.. code-block:: fortran

      subroutine func()

      use mod1, only: var1
      use mod2, only: var3

      implicit none

      integer :: i, j

      i = var1
      j = var3

      end

Remove implicit variable
*********************************

Implicit declaration of variable were common but lead to unclarity in the code. 
We can remove all implicit declaration  and automatically declare variables. For example the code 

.. code-block:: fortran

      subroutine func()

      use mod1, only: var1
      use mod2, only: var2

      implicit real*8(a-h,o-z)

      x = var1
      y = var2

      i = 2
      
      end

implicitly declare variables `x`, `y` and `i`. We can make the declaration implicit with :

.. code-block:: console

  python refac_fortran.py --action clean_implicit --filename ../example/test_implicit.f 

Leading to :

.. code-block:: fortran


      subroutine func()

      use mod1, only: var1
      use mod2, only: var2

      use precision_kinds, only: dp
      implicit none

      integer :: i
      real(dp) :: x, y

      x = var1
      y = var2

      i = 2
      
      end
Note that the `precision_kinds` module needs to be created separately to look like:

.. code-block:: fortran

 module precision_kinds
    implicit none
   ! named constants for 4, 2, and 1 byte integers:
   integer, parameter :: &
        i4b = selected_int_kind(9), &
        i2b = selected_int_kind(4), &
        i1b = selected_int_kind(2)
   ! single, double and quadruple precision reals:
   integer, parameter :: &
        sp = kind(1.0), &
        dp = selected_real_kind(2 * precision(1.0_sp)), &
        qp = selected_real_kind(2 * precision(1.0_dp))
 end module precision_kinds


Move variable in new module
*********************************

During refactoring of large code base it is sometimes useful to move variable from one module to another.
For example in the following code :

.. code-block:: fortran


      subroutine func()

      use mod1, only: var1, var3, var5
      use mod2, only: var2, var7
      
      implicit real*8(a-h,o-z)

      x = var1
      y = var2

      i = 2
      
      end

We might wish to move `var3` to a new module called `modx`. This can be done with

.. code-block:: console

  python refac_fortran.py --action move_var --var_name var3 --new_module modx --filename ../example/test_move_var.f 

Leading to :

.. code-block:: fortran


      subroutine func()

      use mod1, only: var1, var5
      use mod2, only: var2, var7
      use modx, only: var3

      implicit real*8(a-h,o-z)

      x = var1
      y = var2

      i = 2
      
      end

Note that you need to move the variable from `mod1` to `modx` in the module file separately.

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
