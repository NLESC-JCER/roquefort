      subroutine func()

      use mod1, only: var1, var3, var5
      use module2, only: var2, var7
      use mod1, only: var1, var3, var5
      use module2, only: var4
      use very_long_module_name, only: longvar1
      use xmod1, only: var8, var9
      use xmod2

      implicit none

      x = var1
      y = var2

      i = 2

      end
