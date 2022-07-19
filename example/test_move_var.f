
      module test_module
      contains
      subroutine func1()

      use mod0, only: x
      use mod1, only: var1, var3, var5
      use mod2, only: var2, var7 ! sasa
      
      
      implicit real*8(a-h,o-z)

      x = var1
      y = var2

      i = 2
      
      end

      subroutine func2()

      use mod3, only: var3, a, b
      use mod4, only: z
      use mod3, only: var2 
      
      implicit real*8(a-h,o-z)

      u = sin(x)
      
      end

      subroutine func3()

      use mod5, only: u, v
      use mod6, only: asterix
      
      implicit real*8(a-h,o-z)

      u = cos(x)
      
      end

      end module


      module test_module2
      contains
      subroutine func1()
      
      use mod0, only: x
      use mod1, only: var1, var3, var5
      use mod2, only: var2, var7 ! sasa

      
      implicit real*8(a-h,o-z)

      x = var1
      y = var2

      i = 2
      
      end

      subroutine func2()

      use mod3, only: var3, a, b
      use mod4, only: z
      
      implicit real*8(a-h,o-z)

      u = sin(x)
      
      end

      subroutine func3()

      use mod5, only: u, v
      use mod6, only: asterix
      
      implicit real*8(a-h,o-z)

      u = cos(x)
      
      end

      end module
