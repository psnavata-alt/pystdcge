$STITLE Input file: DIAGNOSTICS.INC. Standard CGE modeling system, Version 1.01

$ontext

This is an optional include file for mod.gms. It displays and generates
information that may be useful when debugging a model. Some of this
information was generated in MOD.GMS and its include files. Some of
the information is created in this file.

$offtext


$ontext

COMMENTS ON THE INFORMATION THAT APPEARS IN THE FILE DIAGNOSTICS.INC
====================================================================

This file includes the following sections (with searchable headings):


ILLEGAL SAM PAYMENTS OR VALUES

Error message if illegal payment flows appear in SAM
(which simply may reflect errors in data entry). Solutions if errors are
generated:
(1) change/restructure the SAM (typically the preferred approach);
(2) restructure the model (typically more complicated).

The model structure assumes that imports are not reexported, i.e. that
exports stem from domestic production. Accordingly, an error message is
generated if, for any commodity, exports exceeds domestic production.
Solutions if errors are generated:
(1) if there is data error, correct it;
(2) if substantial reexportation takes place, create a reexporting
activity that, as inputs, use primary factors and an imported
intermediate commmodity without domestic production. All of its outputs
should be exported.


SAMBALCHK

If the SAM that is used as the model database is unbalanced, the model
will fail to replicate the SAM and may not solve. Such imbalances are
typically due to errors made when introducing changes in the SAM after
the running of the SAM-balancing program in SAMBAL.INC.


NEGCELL

For a subset of the cells, negative entries are legal. However, entries
that are negative as a result of coding mistakes are a common source of
errors. The two-dimensional NEGCELL set has elements for all cells with
negative entries. Verify that there are no errors.


MAXCELL, MINCELL, LARGECELL AND SMALLCELL

A badly scaled SAM may make it more difficult to solve the model. The
parameters MAXCELL and MINCELL displays the maximum and minimum absolute
cell values in the SAM. The two-dimesional sets LARGECELL and SMALLCELL
indicate the payments flows in the SAM that are 'large' and 'small',
respectively.

If the value of MAXCELL exceeds 10**3 the user may consider
rescaling the SAM in the country data file (by dividing all SAM values
by 10 raised to a power such that the maximum cell value is less than
10**3.

Rescaling will reduce small cell values which may be another source of
difficulties. To eliminate small (absolute) cell values in the SAM
balancing program (in SAMBAL.INC) by increasing the value of the scalar
CUTOFF above zero.


SMALL TRADE AND VALUE-ADDED SHARES

On the basis of the information in the SAM, model parameters define
--commodity trade shares (for each commodity, the share of exports in
total output, and the shares of import in total domestic demand); and
--activity value-added shares (the share of each factor in the value-added
of each activity in which the factor is used).

If these shares are small (let's say smaller than 0.001), evaluation
errors are likely.

If trade shares are small, one remedy is to eliminate the payment from
the SAM (since it is small, it is typically unlikely to have much
influence on the results). The same approach may be applied for the case
of small value-added shares. For both trade and value-added shares, the
problem may be mitigated if the SAM is aggregated (across activities,
commodities and/or factors).

Similarly, the presence of activities that have a very small share of
total economywide value-added may be a source of errors since such
activities tend to have very small quantities for factor demands,
intermediate demands, and output. In this case, the recommended action
is to aggregate across activities.

For aggregation, the file SAMAGG.GMS may be used.


MISSING OR INCORRECT NON-SAM DATA

Error messages will be generated if data are missing or incorrect.
Examples of sources of errors: missing trade or production elasticities;
data for factor quantity use only supplied for a subset of the
activities that, according to the SAM, use a given factor; non-SAM share
data that should sum to unity do not.

$offtext



*ILLEGAL SAM PAYMENTS OR VALUES============================

PARAMETER
 ERRSAMFLOW(AC,ACP) if UNDF -- illegal SAM payment from 2nd index to 1st
 ERREXPOUT(C)       if UNDF -- exports exceed domestic output for comm c
 ;

*Activities (A) are not permitted to pay to institutions (INS) or other
*activities (AP).
 ERRSAMFLOW(INS,A)$SAM(INS,A)     = 1/0;
 ERRSAMFLOW(AP,A)$SAM(AP,A)       = 1/0;

*Commodities (C) are not permitted to pay to factors (F) or domestic
*institutions (INSD).
 ERRSAMFLOW(F,C)$SAM(F,C)         = 1/0;
 ERRSAMFLOW(INSD,C)$SAM(INSD,C)   = 1/0;

*Factors (F) are not permitted to pay to activities (A), commodities (C)
*or other factors (FP).
 ERRSAMFLOW(A,F)$SAM(A,F)         = 1/0;
 ERRSAMFLOW(C,F)$SAM(C,F)         = 1/0;
 ERRSAMFLOW(FP,F)$SAM(FP,F)       = 1/0;

*Domestic institutions (INSD) are not permitted to pay to factors (F).
 ERRSAMFLOW(F,INSD)$SAM(F,INSD)   = 1/0;

*Government (GOV) and the rest of the world (ROW) are not permitted to
*pay to activities (A).
 ERRSAMFLOW(A,'GOV')$SAM(A,'GOV') = 1/0;
 ERRSAMFLOW(A,'ROW')$SAM(A,'ROW') = 1/0;

*Enterprises (EN) are not permitted to pay to activities (A) or
*commodities (C).
 ERRSAMFLOW(A,EN)$SAM(A,EN)       = 1/0;
 ERRSAMFLOW(C,EN)$SAM(C,EN)       = 1/0;

SET
 SIREC(AC) set for elements permitted to receive payment from S-I;
 SIREC(C) = YES;  SIREC('DSTK') = YES;

*Savings-investment (S-I) account is only permitted to pay to accounts
*for commodities (C) and stock change (DSTK)
 ERRSAMFLOW(ACNT,'S-I')$(SAM(ACNT,'S-I') AND (NOT SIREC(ACNT))) = 1/0;

*Savings-investment (S-I) account is only permitted to receive payments
*from institutions (INS)
 ERRSAMFLOW('S-I',ACNT)$(SAM('S-I',ACNT) AND (NOT INS(ACNT)))       = 1/0;

*Stock change account (DSTK) is only permitted to receive payments from
*savings-investment (S-I) and make payments to commodities (C).
 ERRSAMFLOW('DSTK',ACNT)$(SAM('DSTK',ACNT) AND (NOT ACNT('S-I')))   = 1/0;
 ERRSAMFLOW(ACNT,'DSTK')$(SAM(ACNT,'DSTK') AND (NOT C(ACNT)))       = 1/0;

*It is illegal to have import tariffs for commodities without imports
 ERRSAMFLOW('IMPTAX',C)$(TAXPAR('IMPTAX',C) AND (NOT SAM('ROW',C))) = 1/0;

*It is illegal to have export taxes for commodities without exports
 ERRSAMFLOW('EXPTAX',C)$(TAXPAR('EXPTAX',C) AND (NOT SAM(C,'ROW'))) = 1/0;


*Value of exports is greater than the value of domestic production. Note that
*exports can equal to value of domestic production, so test includes 1E-6.
 ERREXPOUT(C)$(SAM(C,'ROW') GT (SUM(A, SAM(A,C)) + TAXPAR('EXPTAX',C)
                                   + SUM(CTE, SAM(CTE,C)) + 1.E-6)) = 1/0 ;
DISPLAY
 ERRSAMFLOW
 ERREXPOUT
"The model structure assumes that exports are produced domestically,"
"i.e., not reexported imports. The model will not work if exports"
"exceed domestic output."
;


*SAMBALCHK=================================================

PARAMETER
 SAMGAPCUTOFF  max acceptable abs gap bt model SAM row and col totals
 ERRSAMBAL(AC) if UNDF -- the absolute imbalance for AC exceeds cutoff
 ;

 SAMGAPCUTOFF = 1.0e-5;

 ERRSAMBAL(AC)$(ABS(SAMBALCHK(AC)) GT SAMGAPCUTOFF) = 1/0;

DISPLAY
 SAMBALCHK
"Note: The last definition of SAMBALCHK is in the MOD.GMS file. To find"
"it search for 'SAM after final adjustments'."
""
 SAMGAPCUTOFF
 ERRSAMBAL
"Note: If the SAM that is used as the model database is unbalanced"
"the model will fail to replicate the SAM and may not solve."
"Here absolute imbalance values in excess of the value of SAMGAPCUTOFF"
"generate an error for the parameter ERRSAMBAL."
 ;


*NEGCELL===================================================

$ontext
Check on negative SAM entries It is legal to have negative entries in a
SAM. However, entries that are negative as a result of coding mistakes
are a common source of errors. The following set has elements for all
cells with negative entries. Verify that there are no errors.
$offtext

SET
 NEGCELL(AC,ACP) the SAM payment from ACP (column) to AC (row) is negative
 ;

 NEGCELL(AC,ACP)$(SAM(AC,ACP) LT 0) = YES;

DISPLAY
 NEGCELL
"Note: Unintended negative cell entries can be a source of errors."
 ;


*MAXCELL, MINCELL, LARGECELL AND SMALLCELL=================

$ontext

A badly scaled SAM may make it more difficult to solve the model. The
following segment generates information about maximum and minimum
absolute cell values as well as the location of large and small cells.
Note that no action is taken and no errors generated. This section only
provides information.

If the maximum absolute cell value exceeds 10**3 the user may consider
rescaling the SAM in the country data file (by dividing all SAM values
by 10 raised to a power such that the maximum cell value is less than
10**3). This may be done immediately after that the SAM parameter is
defined.

Rescaling will also reduce small cell values which may be another source
of difficulties. If so, the user may activate the option of eliminating
small (absolute) cell values in the SAM balancing program (in
SAMBAL.INC) by increasing the value of the scalar CUTOFF above zero.

$offtext

SCALAR
 MAXCELL     maximum absolute cell value in SAM (excluding totals)
 MINCELL     minimum absolute non-zero cell value in SAM
;

 MAXCELL = SMAX((ACNT,ACNTP), ABS( SAM(ACNT,ACNTP) ));
 MINCELL = SMIN((ACNT,ACNTP)$SAM(ACNT,ACNTP), ABS( SAM(ACNT,ACNTP) ));


SET
 LARGECELL(AC,ACP) cells with absolute values larger than cellcutoffup
 SMALLCELL(AC,ACP) cells with absolute values smaller than cellcutofflo
 ;

PARAMETER
 cellcutoffup absolute cell values above cutoff are displayed as large
 cellcutofflo absolute cell values below cutoff are displayed as small
 ;

*No cells are large if cellcutoffup is set at +INF.
*cellcutoffup = +INF;
 cellcutoffup = 1000;

*No cells are small if cellcutofflo is set at zero.
*cellcutofflo = 0;
 cellcutofflo = 0.01;

 LARGECELL(AC,ACP)$(ABS(SAM(AC,ACP)) GT cellcutoffup) = YES;

 SMALLCELL(AC,ACP)$(SAM(AC,ACP) AND (ABS(SAM(AC,ACP)) LT cellcutofflo))
   = YES;


DISPLAY
 MAXCELL, MINCELL, LARGECELL, SMALLCELL, cellcutoffup, cellcutofflo
"Note: A (badly scaled) SAM with very large and/or very small (absolute)"
"cell values can be a source of errors. 'Large' and 'small' values are"
"perhaps best defined as larger and smaller than 10000 and 0.01, resp."
"Here cells with values above/below cellcutoffup/cellcutofflo are"
"defined as large/small."
 ;


*SMALL TRADE AND VALUE-ADDED SHARES========================

PARAMETERS
 ACTFACSHR(F,A) small share of factor f in total value-added of activity a
 ACTVASHR(A)    small share of activity a in total economywide value-added
 EXPSHR(C)      small share of exports in total output of commodity c
 IMPSHR(C)      small share of imports in total domestic demand for commodity c
 ;

 ACTFACSHR(F,A)$SUM(FP, SAM(FP,A)) = SAM(F,A) / SUM(FP, SAM(FP,A));
 ACTVASHR(A)$SUM((F,AP), SAM(F,AP))    = SUM(F, SAM(F,A)) / SUM((F,AP), SAM(F,AP));

 EXPSHR(C)$SUM(A, SAM(A,C))
  = (SAM(C,'ROW') - TAXPAR('EXPTAX',C) - SUM(CTE, SAM(CTE,C)))
    / SUM(A, SAM(A,C));

 IMPSHR(C)$(SAM(C,'TOTAL') - SAM(C,'ROW') - TAXPAR('COMTAX',C))
  = (SAM('ROW',C) + TAXPAR('IMPTAX',C) + SUM(CTM, SAM(CTM,C)))
    / (SAM(C,'TOTAL') - SAM(C,'ROW') - TAXPAR('COMTAX',C));


SET
 SHRITEM items for which shares and cutoffs are defined
 /FAC factor in activity, VA value-added, EXP exports , IMP imports/

PARAMETER
 SHRCUTOFF(SHRITEM)  upper limit for shares values that are displayed
 ;
 SHRCUTOFF('FAC') = 0.005;
 SHRCUTOFF('VA')  = 0.005;
 SHRCUTOFF('EXP') = 0.005;
 SHRCUTOFF('IMP') = 0.005;

*If SHRCUTOFF is set at 1 or larger, no shares are eliminated from display
SHRCUTOFF(SHRITEM) = 1;

*Eliminating shares that are above the cutoff from display.
 ACTFACSHR(F,A)$(NOT (ACTFACSHR(F,A) LT SHRCUTOFF('FAC'))) = 0;
 ACTVASHR(A)$(NOT (ACTVASHR(A) LT SHRCUTOFF('VA')))        = 0;
 EXPSHR(C)$(NOT (EXPSHR(C) LT SHRCUTOFF('EXP')))           = 0;
 IMPSHR(C)$(NOT (IMPSHR(C) LT SHRCUTOFF('IMP')))           = 0;

DISPLAY
SHRCUTOFF
"Small shares may be a source of function evaluation errors in model"
"simulations. For the following parameters (ACTFACSHR, ACTVASHR,"
"EXPSHR, IMPSHR), shares smaller than SHRCUTOFF shrcutoff are defined"
"as 'small'."
""
ACTFACSHR, ACTVASHR, EXPSHR, IMPSHR,
"'Small' shares are displayed for ACTFACSHR, ACTVASHR, EXPSHR, IMPSHR."
;


*MISSING OR INCORRECT NON-SAM DATA=========================

*Error messages will be generated if data are missing or incorrect.

PARAMETERS
 ERRHOME(A,H)    act with home cons comm shares not summing to one
 ERRQFBASE1(F,A) demand specified for factor but no SAM payment
 ERRQFBASE2(F,A) demands specified but missing for f-a combination in SAM
 ERRTRADE(C,TRDELAS)  commodities with missing trade elas
 ERRPROD1(A)     activities with missing factor substitut elas
 ERRPROD2(A)     CES activities with missing agg va - intermed elas
 ERRAC(C)        commodities with missing domestic aggregation elas
 ERRLES1(C,H)    marketed commodities with missing hhd cons elas
 ERRLES2(A,C,H)  home comm's with shrhome but missing hhd cons elas
  ;


*Parameter with error in data provided: SHRHOME(A,C,H)
 ERRHOME(A,H)$(SAM(A,H)$(SUM(C, SHRHOME(A,C,H))
                      $((SUM(C, SHRHOME(A,C,H)) NE 1)))) = 1/0;

*Parameter with missing data: SAM (or error in QFBASE)
 ERRQFBASE1(F,A)$(QFBASE(F,A)$(NOT SAM(F,A))) = 1/0;

*Parameter with missing data: QFBASE
 ERRQFBASE2(F,A)
   $(SAM(F,A)$((NOT QFBASE(F,A))$SUM(AP, QFBASE(F,AP)))) = 1/0;

*Parameter with missing data: TRDELAS
 ERRTRADE(C,'SIGMAQ')$((CM(C)AND CD(C))$(TRADELAS(C,'SIGMAQ')EQ 0)) = 1/0;
 ERRTRADE(C,'SIGMAT')$((CE(C)AND CD(C))$(TRADELAS(C,'SIGMAT')EQ 0)) = 1/0;

*Parameters with missing data: PRODELAS and-or PRODELAS2
 ERRPROD1(A)$((PRODELAS(A) EQ 0) AND SAM('TOTAL',A)) = 1/0;
 ERRPROD2(ACES)$((PRODELAS2(ACES) EQ 0) AND SAM('TOTAL',ACES)) = 1/0;

*Parameter with missing data: ELASAC
 ERRAC(C)$(SUM(A, SAM(A,C))$(ELASAC(C) EQ 0)) = 1/0;

*Parameter with missing data: LESELAS1
 ERRLES1(C,H)$(SAM(C,H)$(LESELAS1(H,C) EQ 0)) = 1/0;

*Parameter with missing data: LESELAS2
 ERRLES2(A,C,H)$(SHRHOME(A,C,H)$(LESELAS2(A,C,H) EQ 0)) = 1/0;

DISPLAY
 ERRHOME
"Note: For ERRHOME, the error is due to user-defined values for"
"SHRHOME. If the user does not define any values, the program generates"
"data for SHRHOME. These are correct as long as home consumption is for"
"commodities produced by single-output activites."
 ERRQFBASE1, ERRQFBASE2
 ERRTRADE, ERRPROD1, ERRPROD2, ERRAC, ERRLES1, ERRLES2;


*#*#*#*#*# THE END OF DIAGNOSTICS.INC #*#*#*#*