
      subroutine func()

      use mod1, only: var1
      use mod2, only: var2

      implicit real*8(a-h,o-z)

      x = var1
      y = var2

      i = 2
      
      end