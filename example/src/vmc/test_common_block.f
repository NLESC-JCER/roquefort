      subroutine func()


      use mod1, only: var1, var2
      implicit real*8(a-h,o-z)


      common /mod2/ var3, var4
      

      x = var1
      y = var2

      i = 2
      
      end
