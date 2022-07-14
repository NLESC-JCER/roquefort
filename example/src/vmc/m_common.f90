
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

 module numbas
   !> Arguments: arg, d2rwf, igrid, iwrwf, nr, nrbas, numr, r0, rwf

   use precision_kinds, only: dp
   include 'vmc.h'

    real(dp) :: arg(MCTYPE)
    real(dp) :: d2rwf(MRWF_PTS,MRWF,MCTYPE,MWF)
    integer  :: igrid(MCTYPE)
    integer  :: iwrwf(MBASIS,MCTYPE)
    integer  :: nr(MCTYPE)
    integer  :: nrbas(MCTYPE)
    integer  :: numr
    real(dp) :: r0(MCTYPE)
    real(dp) :: rwf(MRWF_PTS,MRWF,MCTYPE,MWF)
    private

    public :: arg, d2rwf, igrid, iwrwf, nr, nrbas, numr, r0, rwf

    save
 end module numbas
