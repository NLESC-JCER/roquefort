
 module numexp
   !> Arguments: ae, ce
   use precision_kinds, only: dp
   include 'vmc.h'

    real(dp) :: ae(2,MRWF,MCTYPE,MFORCE)
    real(dp) :: ce(NCOEF,MRWF,MCTYPE,MFORCE)
    private

    public :: ae, ce
    save
 end module numexp
