
      subroutine func()

      use mod1, only: var1, var2
      use mod2, only: var3

      implicit none

      integer :: i, j

      i = var1
      j = var3

      end