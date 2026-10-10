$TITLE Code for lower variable limits. Standard CGE modeling system, Version 1.00
$ontext

Version 1.00 Release date: May 02, 2001
Last update:

This file is optional. For selected variables, a lower limit is
imposed. This may improve solver performance. The variables that are
selected:
(i) are associated with equations of the same dimension (in the model
    definition)
(ii) should never have equilibrium values equal to or below zero.

The lower limit may be varied by changing the definition of LOWLIM.

$offtext

SCALAR
 LOWLIM  lower limit for selected variables /0.0001/;
*The selected variables are associated with equations
*of the same dimension

*Price block
 PM.LO(C)$PM0(C)           = LOWLIM;
 PE.LO(C)$PE0(C)           = LOWLIM;
 PQ.LO(C)$PQ0(C)           = LOWLIM;
 PX.LO(C)$PX0(C)           = LOWLIM;
 PDD.LO(C)$PDD0(C)         = LOWLIM;
 PA.LO(A)$PA0(A)           = LOWLIM;
 PINTA.LO(A)$PINTA0(A)     = LOWLIM;
 PVA.LO(A)$PVA0(A)         = LOWLIM;

*Production and trade block
 QVA.LO(A)$QVA0(A)         = LOWLIM;
 QINT.LO(C,A)$QINT0(C,A)   = LOWLIM;
 PXAC.LO(A,C)$PXAC0(A,C)   = LOWLIM;
 QX.LO(C)$QX0(C)           = LOWLIM;
 QXAC.LO(A,C)$QXAC0(A,C)   = LOWLIM;
 QT.LO(C)$QT0(C)           = LOWLIM;

*Institution block
 YF.LO(F)$YF0(F)           = LOWLIM;
 YIF.LO(INS,F)$YIF0(INS,F) = LOWLIM;
 YI.LO(INS)$YI0(INS)       = LOWLIM;
 EH.LO(H)                  = LOWLIM;
 TRII.LO(INS,INSP)$TRII0(INS,INSP) = LOWLIM;
 QH.LO(C,H)$QH0(C,H)       = LOWLIM;
 QHA.LO(A,C,H)$QHA0(A,C,H) = LOWLIM;
 EG.LO                     = LOWLIM;
 YG.LO$YG0                 = LOWLIM;
 QG.LO(C)$QG0(C)           = LOWLIM;
 QINV.LO(C)$QINV0(C)       = LOWLIM;

*System-constraint block
 TINS.LO(INS)$TINS0(INS)   = LOWLIM;
 MPS.LO(INS)$MPS0(INS)     = LOWLIM;
 TABS.LO                   = LOWLIM;


$ontext
* CPI.LO                    = LOWLIM;
* DMPS.LO                   = LOWLIM;
* DPI.LO                    = LOWLIM;
* DTINS.LO                  = LOWLIM;
* EXR.LO                    = LOWLIM;
* FSAV.LO                   = LOWLIM;
* GADJ.LO                   = LOWLIM;
* GOVSHR.LO                 = LOWLIM;
* GSAV.LO                   = LOWLIM;
* IADJ.LO                   = LOWLIM;
* INVSHR.LO                 = LOWLIM;
* MPSADJ.LO                 = LOWLIM;
  PDS.LO(C)$PDS0(C)         = LOWLIM;
  PWE.LO(C)$PWE0(C)         = LOWLIM;
  PWM.LO(C)$PWM0(C)         = LOWLIM;

  QA.LO(A)$QA0(A)           = LOWLIM;
  QD.LO(C)$QD0(C)           = LOWLIM;
  QE.LO(C)$QE0(C)           = LOWLIM;
  QF.LO(F,A)$QF0(F,A)       = LOWLIM;
  QFS.LO(F)$QFS0(F)         = LOWLIM;


  QINTA.LO(A)$QINTA0(A)     = LOWLIM;

  QM.LO(C)$QM0(C)           = LOWLIM;
  QQ.LO(C)$QQ0(C)           = LOWLIM;


* TINSADJ.LO                = LOWLIM;
* WALRAS.LO                 = LOWLIM;
  WF.LO(F)$WF0(F)           = LOWLIM;
  WFDIST.LO(F,A)$WFDIST0(F,A)   = LOWLIM;
$offtext
