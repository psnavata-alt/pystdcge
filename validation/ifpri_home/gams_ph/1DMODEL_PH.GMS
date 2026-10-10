$STITLE Input file: 1dmodel.gms. IFPRI Extended standard recursive dynamic CGE modeling system, Version 2.00
$ontext
ALTERED VERSION (GNU GPL v2, condition 2). Modified copy of IFPRI's 1dmodel.gms (Version 2.00), made on
2 Oct 2026 for pystdcge validation (route A), with Claude Code.
Changes: (1) the data file is 1MODEL_PH.DAT (condensed Philippine SAM) instead of 1MODEL.DAT;
(2) a validation block is APPENDED at the end; (3) 8 Oct 2026, home-consumption run: the report
adds home consumption (QHA at base producer prices) to real GDP and consumption and reports it separately (test shocks under two closures; results written to
ifpri_results.csv). No model equation, parameter definition or calibration statement is changed.
$offtext

$ONSYMLIST ONSYMXREF OFFUPPER
*$OFFSYMLIST OFFSYMXREF
$ONEMPTY
*The dollar control option makes empty data initialization statements
*permissible (e.g. sets without elements or parameters without data)

$ontext
This file extends the IFPRI static model into a Standard Recursive Dynamic
CGE Model.

The recursive dynamic model is documented in:

Thurlow, J. 2004. A Dynamic Computable General Equilibrium (CGE) Model
for South Africa: Extending the Static IFPRI Model. Trade and Industial
Policy Strategies, Johannesburg.

The static model is documented in:

Lofgren, Hans, Rebecca Lee Harris, and Sherman Robinson, with the
assistance of Moataz El-Said and Marcelle Thomas. 2002. A Standard
Computable General Equilibrium (CGE) Model in GAMS. Microcomputers in
Policy Research, Vol. 5. Washington, D.C.: IFPRI.

Copyright (c) 2002, International Food Policy Research Institute (IFPRI),
Washington, DC.

For additional information on the model and the GAMS files, see
also the file README.TXT.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public Licence, version 2, as
published by the Free Software Foundation.

This progrm is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public Licence for more details.

Under the GNU General Public Licence, permission is granted to anyone to
use this software for any purpose, including commercial applications,
and to alter it and redistribute it freely, subject to the following
restrictions:
(1) The origin of this software must not be misrepresented; you must not
    claim that you wrote the original software. If you use this software
    in a product, an acknowldgement in the product documentation would be
    appreciated.
(2) Altered source versions must be plainly marked as such, and must not be
    misrepresented as being the original software.
(3) This notice may not be removed or altered from any source distribution.

See the GNU General Public Licence for more details. A copy of the GNU
General Public Licence may be obtained from:
  Free Software Foundation, Inc.
  59 Temple Place, Suite 330
  Boston, MA 02111-1307

or from their website: http://www.gnu.org/copyleft/gpl.html

Only experienced users should make changes in files other than the
country-specific data sets. If changes are made, it is good modeling
practice to carefully document these so well that another user (or the
original user, one year later) can understand what was done.
$offtext


*--------------------------------------------------------------------------------------------
*1. SET DECLARATIONS ------------------------------------------------------------------------
*--------------------------------------------------------------------------------------------

$ontext
In this section, all sets are declared. They are divided into the
following groups:
a. model sets (appearing in the model equations)
b. calibration sets (used to initialize variables and define model
   parameters)
c. report sets (used in report files)
$offtext

SETS
*a. model sets
 AC           global set for model accounts - aggregated microsam accounts
 ACNT(AC)     all elements in AC except TOTAL
 AAG(AC)      aggregate activity accounts
 R(AC)        trading regions
 A(AC)        activities
 ACES(A)      activities with CES fn at top of technology nest
 ALEO(A)      activities with Leontief fn at top of technology nest
 C(AC)        commodities
 CD(C)        commodities with domestic sales of output
 CDN(C)       commodities without domestic sales of output
 CE(C)        exported commodities
 CER(C,R)     imported commodities by region
 CEN(C)       non-export commodities
 CM(C)        imported commodities
 CMR(C,R)     imported commodities by region
 CMN(C)       non-imported commodities
 CX(C)        commodities with output
 F(AC)        factors
 FAGG(F)      aggregate factors in factor nesting
 FLAB(F)      labor
 FLND(F)      land
 FCAP(F)      capital
 FDIS(F)      disaggregate factors
 FNEST(F,F)   nested structure of factors
 FTREE(F,F,F) nested structure of factors
 GOVF         government functions for expenditure
 MFA1(F,A)    factor F (agg or disagg) is used by A at top of nest
 MFA2(F,F,A)  factor FP is aggregated to factor F for activity A
 INS(AC)      institutions
 INSD(INS)    domestic institutions
 INSDNG(INSD) domestic non-government institutions
 EN(INSDNG)   enterprises
 H(INSDNG)    households
 HAGG(H)      aggregate households
*b. calibration sets
 CINV(C)      fixed investment goods
 CT(C)        transaction service commodities
 CTD(AC)      domestic transactions cost account
 CTE(AC)      export transactions cost account
 CTM(AC)      import transactions cost account
*c. report sets
 AAGR(A)      agricultural activities
 AMIN(A)      mining activities
 AIND(A)      industrial activities
 ASER(A)      service activities
 ANAGR(A)     non-agricultural activities
 CAGR(C)      agricultural commodities
 CMIN(C)      mining commodities
 CIND(C)      industrial commodities
 CSER(C)      service commodities
 CNAGR(C)     non-agricultural commodities
 HURB(H)      urban households
 HRUR(H)      rural households
*d. mappings
 MAPAAGA(AAG,A) aggregate activities to region-specific activities
 MAPA2C(A,C)  direct mapping between activities and commodities
;

*ALIAS statement to create identical cets
ALIAS
 (AC,ACP)   , (ACNT,ACNTP), (A,AP,APP)
 (C,CP,CPP) , (CE,CEP)    , (CM,CMP)
 (F,FP,FPP) , (FAGG,FAGGP), (FLAB,FLABP), (FCAP,FCAPP)    , (FLND,FLNDP)    , (GOVF,GOVFP)
 (INS,INSP) , (INSD,INSDP), (INSDNG,INSDNGP), (H,HP), (R,RP)
;

*--------------------------------------------------------------------------------------------
*2. DATABASE --------------------------------------------------------------------------------
*--------------------------------------------------------------------------------------------

PARAMETER
 SAM(AC,ACP)     standard SAM
 NEST(F,FP)      nested structure of factors in the model
 TREE(F,FP)      direct and indirect factor mapping in nested factor structure
 SAMBALCHK(AC)   column minus row total for SAM
;

*INCLUDE ONE COUNTRY DATA SET
*Remove asterisk in front of ONE (AND ONLY ONE) of the following lines
*or add a new line for new file with country data

$INCLUDE 1MODEL_PH.DAT

*SAM adjustments ----------------------------------------------------

*In this section, some minor adjustments are made in the SAM (when
*needed) to fit the model structure.


*Adjustment for sectors with only exports and no domestic sales.
*If there is a very small value for domestic sales, add the discrepancy
*to exports.

*Netting transfers between domestic institutions and RoW.
 SAM(INSD,'ROW')   = SAM(INSD,'ROW') - SAM('ROW',INSD);
 SAM('ROW',INSD)   = 0;

*Netting transfers between factors and RoW.
 SAM('ROW',F)  = SAM('ROW',F) - SAM(F,'ROW');
 SAM(F,'ROW')  = 0;

*Netting transfers between government and domestic non-
*government institutions.
 SAM(INSDNG,'GOV') = SAM(INSDNG,'GOV') - SAM('GOV',INSDNG);
 SAM('GOV',INSDNG) = 0;

*Eliminating payments of any account to itself.
 SAM(ACNT,ACNT) = 0;



*Checking SAM balance ------------------------------------------------

*Account totals are recomputed. Check for SAM balance.
 SAM('TOTAL',ACNT) = SUM(ACNTP, SAM(ACNTP,ACNT));
 SAM(ACNT,'TOTAL') = SUM(ACNTP, SAM(ACNT,ACNTP));

 SAMBALCHK(AC)   = SAM('TOTAL',AC) - SAM(AC,'TOTAL');

 DISPLAY "SAM after final adjustments", SAMBALCHK;
 DISPLAY "SAM after final adjustments", SAM;

*Additional set definitions based on country SAM ---------------------

*CD is the set for commodities with domestic sales of domestic output
*i.e., for which (value of sales at producer prices)
*              > (value of exports at producer prices)
 CD(C)  = YES$(SUM(A, SAM(A,C)) GT (SAM(C,'ROW') - TAXPAR('EXPTAX',C) - SUM(CTE, SAM(CTE,C))) );

 CDN(C) = NOT CD(C);

 CE(C)  = YES$(SAM(C,'ROW'));
 CEN(C) = NOT CE(C);
 CER(C,R)$(CE(C) AND REGEXP(C,R)) = YES;

 CM(C)  = YES$(SAM('ROW',C));
 CMN(C) = NOT CM(C);
 CMR(C,R)$(CM(C) AND REGIMP(C,R)) = YES;

 CX(C) = YES$SUM(A, SAM(A,C));

 CT(C)$(SUM(CTD, SAM(C,CTD)) + SUM(CTE, SAM(C,CTE)) + SUM(CTM, SAM(C,CTM)))  = YES;

*If activity has no intermediate inputs, then Leontief function has to
*be used at the top of the technology nest
 ACES(A)$(NOT SUM(C, SAM(C,A))) = NO;
 ALEO(A)$(NOT ACES(A)) = YES;


DISPLAY
 R, CD, CDN, CE, CEN, CER, CM, CMN, CMR, CX, CT, ACES, ALEO, FLS;


*Fine-tuning non-SAM data -------------------------------------------

*Generating missing data for home consumption ---

*If SAM includes home consumption but NO data were provided for SHRHOME,
*data are generated assuming that the value shares for home consumption
*are identical to activity output value shares.

IF(SUM((A,H), SAM(A,H)) AND NOT SUM((A,C,H), SHRHOME(A,C,H)),

 SHRHOME(A,C,H)$(SAM(A,H) AND SUM(CP, SAM(A,CP))) = SAM(A,C)/SUM(CP, SAM(A,CP));

DISPLAY
 "Default data used for SHRHOME -- data missing"
 SHRHOME
 ;
*End IF statement
 );


*Eliminating superfluous elasticity data -------

 TRADELAS(C,'SIGMAT')$(CEN(C) OR (CE(C) AND CDN(C))) = 0;
 TRADELAS(C,'SIGMAQ')$(CMN(C) OR (CM(C) AND CDN(C))) = 0;

 PRODELAS(A)$(NOT SAM('TOTAL',A))     = 0;

 ELASAC(C)$(NOT SUM(A, SAM(A,C)))     = 0;

 LESELAS1(H,C)$(NOT SAM(C,H))         = 0;
 LESELAS2(A,C,H)$(NOT SHRHOME(A,C,H)) = 0;


*Diagnostics ------------------------------------

*Include file that displays and generates information that may be
*useful when debugging data set.
$INCLUDE 1DIAGNOSTICS.INC

*Physical factor quantities ---------------------

PARAMETER
 QF2BASE(F,A)  qnty of fac f employed by act a (extracted data)
 ;
*If there is a SAM payment from A to F and supply (but not
*demand) quantities have been defined in the country data file,
*then the supply values are used to compute demand quantities.
 QF2BASE(F,A)$(SAM(F,A)$((NOT QFBASE(F,A))$QFSBASE(F)))
   = QFSBASE(F)*SAM(F,A)/SUM(AP, SAM(F,AP));

*If there is a SAM payment from A to F and neither supply nor
*demand quantities have been defined in the country data file,
*then SAM values are used as quantities
 QF2BASE(F,A)$(SAM(F,A)$((QFBASE(F,A) EQ 0)$(QFSBASE(F) EQ 0)))
                                                    = SAM(F,A);

*If there is a SAM payment from A to F and demand quantities have
*been defined in the country data file, then this information is used.
 QF2BASE(F,A)$QFBASE(F,A) = QFBASE(F,A);

DISPLAY QF2BASE, QFBASE, QFSBASE;

*--------------------------------------------------------------------------------------------
*3. PARAMETER DECLARATIONS ------------------------------------------------------------------
*--------------------------------------------------------------------------------------------

$ontext
This section is divided into the following subsections:
a. Parameters appearing in model equations
b. Parameters used for model calibration (to initialize variables and
   to define model parameters)
In each group, the parameters are declared in alphabetical order.
$offtext

PARAMETERS

*a. Parameters appearing in model equations ---------------

*Parameters other than tax rates
 alphaa(A)         shift parameter for top level CES function
 alphaac(C)        shift parameter for domestic commodity aggregation fn
 alphae(C)         shift parameter for regional exports aggregation fn
 alpham(C)         shift parameter for regional imports aggregation fn
 alphaq(C)         shift parameter for Armington function
 alphat(C)         shift parameter for CET function
 alphava(A)        shift parameter for CES activity production function
 alphava2(F,A)     Lower level factor nesting parameter
 betah(A,C,H)      marg shr of hhd cons on home com c from act a
 betam(C,H)        marg share of hhd cons on marketed commodity c
 cwts(C)           consumer price index weights
 deltaa(A)         share parameter for top level CES function
 deltaac(A,C)      share parameter for domestic commodity aggregation fn
 deltaq(C,R)       share parameter for Armington function
 deltat(C,R)       share parameter for CET function
 deltava(F,A)      share parameter for CES activity production function
 deltava2(F,FP,A)  lower level factor nesting parameter
 dwts(C)           domestic sales price weights
 gammah(A,C,H)     per-cap subsist cons for hhd h on home com c fr act a
 gammam(C,H)       per-cap subsist cons of marketed com c for hhd h
 ica(C,A)          intermediate input c per unit of aggregate intermediate
 inta(A)           aggregate intermediate input coefficient
 iva(A)            aggregate value added coefficient
 icd(C,CP)         trade input of c per unit of comm'y cp produced & sold dom'ly
 ice(C,CP)         trade input of c per unit of comm'y cp exported
 icm(C,CP)         trade input of c per unit of comm'y cp imported
 mps01(INS)        0-1 par for potential flexing of savings rates
 mpsbar(INS)       marg prop to save for dom non-gov inst ins (exog part)
 qdst(C)           inventory investment by sector of origin
 qbarg(C,GOVF)     exogenous (unscaled) government demand by government function
 qbarinv(C)        exogenous (unscaled) investment demand
 rhoa(A)           CES top level function exponent
 rhoac(C)          domestic commodity aggregation function exponent
 rhoe(C)           regional export CES function exponent
 rhom(C)           regional import CES function exponent
 rhoq(C)           Armington function exponent
 rhot(C)           CET function exponent
 rhova(A)          CES activity production function exponent
 rhova2(F,A)       Lower level factor nesting parameter
 shif(INS,F)       share of dom. inst'on i in income of factor f
 shii(INS,INSP)    share of inst'on i in post-tax post-sav income of inst ip
 supernum(H)       LES supernumerary income
 theta(A,C)        yield of commodity C per unit of activity A
 tins01(INS)       0-1 par for potential flexing of dir tax rates
 trnsfr(INS,AC)    transfers fr. inst. or factor ac to institution ins
 tq01(C)           0-1 par for potential fixing of commodity sales taxes
 tqbar(c)          exogenous (unscaled) sales tax rate

*Tax rates (sales tax is endogenous)
 ta(A)             rate of tax on producer gross output value
 te(C,R)           rate of tax on exports
 ter(C,R)          rate of tax on regional exports
 tf(F)             rate of direct tax on factors (soc sec tax)
 tinsbar(INS)      rate of (exog part of) direct tax on dom inst ins
 tm(C,R)           rate of import tariff
 tva(A)            rate of value-added tax

 fprd0(F,A)        productivity of factor f in act a
 fprd(F,A)         productivity of factor f in act a
 ;

*b. Parameters used for model calibration -----------------

$ontext

For model calibration, one parameter is created for each model variable
with the suffix "0" added to the variable name. 0 is also added to the
names of parameters whose values are changed in experiments.

$offtext

PARAMETERS
*Parameters for definition of model parameters
 alphae0(C)        shift parameter for regional export aggregation fn
 alpham0(C)        shift parameter for regional import aggregation fn
 alphava0(A)       shift parameter for CES activity production function
 qdst0(C)          stock change
 qbarg0(C,GOVF)    exogenous (unscaled) government demand
 gammah0(A,C,H)    per-cap subsist cons for hhd h on home com c fr act a
 gammam0(C,H)      per-cap subsist cons of marketed com c for hhd h
 alphaq0(C)        shift parameter for Armington function
 deltaq0(C,R)      share parameter for CET function
 alphat0(C)        shift parameter for Armington function
 deltat0(C,R)      share parameter for CET function

 ta0(A)            rate of tax on producer gross output value
 te0(C,R)          rate of tax on exports
 tf0(F)            rate of direct tax on factors (soc sec tax)
 tins0(INS)        rate of direct tax on domestic institutions ins
 tm0(C,R)          rate of import tariff
 tva0(A)           rate of value-added tax

*Check parameters
  cwtschk          check that CPI weights sum to unity
  dwtschk          check that PDIND weights sum to unity
  shifchk          check that factor payment shares sum to unity

*Parameters for variable initialization
  CPI0             consumer price index (PQ-based)
  DPI0             index for domestic producer prices (PDS-based)
  DMPS0            change in marginal propensity to save for selected inst
  DTINS0           change in domestic institution tax share
  DTQ0             change in sales tax rate
  EG0              total current government expenditure
  EH0(H)           household consumption expenditure
  EXR0             exchange rate
  FSAV0            foreign savings
  GADJ0(GOVF)      government demand scaling factor by function
  MGADJ0           government demand scaling factor
  GOVSHR0(GOVF)    govt consumption share of absorption by function
  MGOVSHR0         govt consumption share of absorption
  GSAV0            government savings
  GDEFGDP0         government deficit as a percentage of GDP
  IADJ0            investment scaling factor (for fixed capital formation)
  INVSHR0          investment share of absorption
  MPS0(INS)        marginal propensity to save for dom non-gov inst ins
  MPSADJ0          savings rate scaling factor
  PA0(A)           output price of activity a
  PDD0(C)          demand price for com'y c produced & sold domestically
  PDS0(C)          supply price for com'y c produced & sold domestically
  PE0(C,R)         price of exports
  PINTA0(A)        price of intermediate aggregate
  PM0(C,R)         price of imports
  PQ0(C)           price of composite good c
  PVA0(A)          value added price
  PWE0(C,R)        world price of exports
  PWM0(C,R)        world price of imports
  PX0(C)           average output price
  PXAC0(A,C)       price of commodity c from activity a
  QA0(A)           level of domestic activity
  QD0(C)           quantity of domestic sales
  QE0(C,R)         quantity of exports
  QF0(F,A)         quantity demanded of factor f from activity a
  QFS0(F)          quantity of factor supply
  QG0(C,GOVF)      quantity of government consumption by government function
  QH0(C,H)         quantity consumed of marketed commodity c by hhd h
  QHA0(A,C,H)      quantity consumed of home commodity c fr act a by hhd h
  QINT0(C,A)       quantity of intermediate demand for c from activity a
  QINTA0(A)        quantity of aggregate intermediate input
  QINV0(C)         quantity of fixed investment demand
  QM0(C,R)         quantity of imports
  QQ0(C)           quantity of composite goods supply
  QT0(C)           quantity of trade and transport demand for commodity c
  QVA0(A)          quantity of aggregate value added
  QX0(C)           quantity of aggregate marketed commodity output
  QXAC0(A,C)       quantity of ouput of commodity c from activity a
  TABS0            total absorption
  TINS0(INS)       rate of direct tax on domestic institutions ins
  TINSADJ0         direct tax scaling factor
  TQ0(C)           sales tax rate
  TQADJ0           scaled sales tax adjustment factor
  TRII0(INS,INSP)  transfers to dom. inst. insdng from insdngp
  WALRAS0          savings-investment imbalance (should be zero)
  WF0(F)           economy-wide wage (rent) for factor f
  WFREAL0(F)       real wage (rent) for factor f
  WFDIST0(F,A)     factor wage distortion variable
  YF0(f)           factor income
  YG0              total current government income
  YIF0(INS,F)      income of institution ins from factor f
  YI0(INS)         income of (domestic non-governmental) institution ins

*Capital stock updating parameters (only used in the simulation file)
  DKAP(FCAP,A)     change in sectoral real capital stock
  DKAPS(FCAP)      change in aggregate real capital stock
  PKAP(FCAP)       price of aggregate capital good by sector of destination
  CAPSHR1(FCAP)    shares of aggregate capital by type (sums to one)
  CAPSHR2(FCAP,A)  sectoral shares of capital by type (rows sum to one)
  CAPSHR1TOT       used to speed up capital accumulation calculations
  CAPSHR2TOT(FCAP) used to speed up capital accumulation calculations
  BMAT(C,FCAP)     shares of investment goods in aggregate capital by type
  BMATTOT          used to speed up capital accumulation calculations
  GFCF             gross fixed capital formation
  RKAP(FCAP,A)     annual rate of growth of sectoral capital stock by type
  RKAPS(FCAP)      annual rate of growth of aggregate capital stock by type
  WFK1AV           average rental on all capital (economywide)
  WFK2AV(FCAP)     average rental on capital by type (across all activities)
  WFDIST2(FCAP,A)  ratio of sectoral to average rental by capital type
  INVSHR1(FCAP)    investment shares by type of capital
  INVSHR2(FCAP,A)  investment shares by sector for each capital type
  NGFCF            GFCF net of exogenous capital adjustments in fixed sectors
  WFDISTADJ(F,A)   WFDIST adjusted to exclude fixed sectors
  WFADJ(F)         WF adjusted to exclude fixed sectors
  beta1            capital mobility parameter by type                              / 3.00 /
  beta2            capital mobility by sector                                      / 3.00 /
;

*--------------------------------------------------------------------------------------------
*4. PARAMETER DEFINITIONS -------------------------------------------------------------------
*--------------------------------------------------------------------------------------------


*All parameters are defined, divided into the same blocks as the
*equations.

*Price block ------------------------------------

$ontext
The prices PDS, PX, and PE  may be initialized at any desired price.
The user may prefer to initialize these prices at unity or, if
he/she is interested in tracking commodity flows in physical units, at
commodity-specific, observed prices (per physical unit). For any given
commodity, these three prices should be identical. Initialization at
observed prices may be attractive for disaggregated agricultural
commodities. If so, the corresponding quantity values reflect physical
units (given the initial price).

The remaining supply-side price, PXAC, and the non-commodity prices, EXR
and PA may be initizalized at any desired level. In practice, it may be
preferable to initialize PXAC at the relevant supply-side price and EXR
and PA at unity.

If physical units are used, the user should select the unit (tons vs.
'000 tons) so that initial price and quantity variables are reasonably
scaled (for example between 1.0E-2 and 1.0E+3) -- bad scaling may cause
solver problems. Initialization at unity should cause no problem as long
as the initial SAM is reasonably scaled.
$offtext

PARAMETER
 PSUP(C) initial supply-side market price for commodity c
;
 PSUP(C) = 1;

 PE0(C,R)$CER(C,R)   = PSUP(C);
 PX0(C)$CX(C)        = PSUP(C);
 PDS0(C)$CD(C)       = PSUP(C);
 PXAC0(A,C)$SAM(A,C) = PSUP(C);

 PA0(A)       = 1;

$ontext
The exchange rate may be initialized at unity, in which case all data are
in foreign currency units (FCU; e.g., dollars). Set the exchange rate at
another value to differentiate foreign exchange transactions, which will
be valued in FCU, and domestic transactions valued in local currency
units (LCU). The SAM is assumed to be valued in LCU, and the exchange rate
is then used to calculate FCU values for transactions with the rest of the
world.
$offtext

 EXR0          = 1 ;

*Activity quantity = payment to activity divided by activity price
*QA covers both on-farm consumption and marketed output
*output GROSS of tax
 QA0(A)        =  SAM('TOTAL',A)/PA0(A) ;

*Unit value-added price = total value-added / activity quantity
*define pva gross of tax
 QVA0(A)         =  (SUM(F, SAM(F,A))+ TAXPAR('VATAX',A)) ;
 PVA0(A)$QVA0(A) =  (SUM(F, SAM(F,A))+ TAXPAR('VATAX',A))/QVA0(A);
 iva(A)$QA0(A)   =  QVA0(A)/QA0(A) ;
 QXAC0(A,C)$SAM(A,C) = SAM(A,C) / PXAC0(A,C);

 QHA0(A,C,H)$SHRHOME(A,C,H) = SHRHOME(A,C,H)*SAM(A,H)/PXAC0(A,C);


*Output quantity = value received by producers divided by producer
*price
*QX covers only marketed output
 QX0(C)$SUM(A, SAM(A,C))
         =  SUM(A, SAM(A,C)) / PX0(C);

*Export quantity = export revenue received by producers
*(ie. minus tax and transactions cost) divided by
*export price.
PARAMETER
 TRESHR(C,R)
;

 TRESHR(C,R)$SUM(RP, SAM(C,'ROW')*REGEXP(C,RP)+TAXPAR('EXPTAX',C)*REGETX(C,RP))
         = (SAM(C,'ROW')*REGEXP(C,R)+TAXPAR('EXPTAX',C)*REGETX(C,R)) / SUM(RP, SAM(C,'ROW')*REGEXP(C,RP)+TAXPAR('EXPTAX',C)*REGETX(C,RP));

 QE0(C,R)$CER(C,R) = (SAM(C,'ROW')*REGEXP(C,R)
                  - TAXPAR('EXPTAX',C)*REGETX(C,R)
                  - SUM(CTE, SAM(CTE,C))*TRESHR(C,R) )/PE0(C,R);

* QE0(C)$SAM(C,'ROW')
*    =  (SAM(C,'ROW') - TAXPAR('EXPTAX',C) - SUM(CTE, SAM(CTE,C)))/PE0(C);

*RoW export price = RoW export payment (in for curr) / export qnty
 PWE0(C,R)$CER(C,R)  = (SAM(C,'ROW')*REGEXP(C,R)/EXR0) / QE0(C,R);
 te0(C,R)$(SAM(C,'ROW')*REGEXP(C,R)) = (TAXPAR('EXPTAX',C)*REGETX(C,R))/(SAM(C,'ROW')*REGEXP(C,R));
 te(C,R)               =  te0(C,R);

*Quantity of output sold domestically = output quantity less quantity
*exported = value of domestic sales divided by domestic supply price
*QD0 covers only marketed output
 QD0(C)$CD(C) =  QX0(C) - SUM(R, QE0(C,R));

*Domestic demander price = demander payment divided by quantity bought
 PDD0(C)$QD0(C)= (PDS0(C)*QD0(C) + SUM(CTD, SAM(CTD,C)))/QD0(C);

*Define import price to equal domestic price so that import and domestic
*units are the same to the purchaser. If no domestic good, set PM to 1.
 PM0(C,R)$CMR(C,R) = PDD0(C) ;
 PM0(C,R)$(QD0(C) EQ 0)  = 1 ;

*Import quantity = demander payment for imports (including tariffs
*and marketing cost) divided by demander price.
*JT: REGIONAL
PARAMETER
 TRMSHR(C,R)
;

 TRMSHR(C,R)$SUM(RP, SAM('ROW',C)*REGIMP(C,RP)+TAXPAR('IMPTAX',C)*REGTAR(C,RP))
         = (SAM('ROW',C)*REGIMP(C,R)+TAXPAR('IMPTAX',C)*REGTAR(C,R)) / SUM(RP, SAM('ROW',C)*REGIMP(C,RP)+TAXPAR('IMPTAX',C)*REGTAR(C,RP));

 QM0(C,R)$CMR(C,R) = (SAM('ROW',C)*REGIMP(C,R)
                  + TAXPAR('IMPTAX',C)*REGTAR(C,R)
                  + SUM(CTM, SAM(CTM,C))*TRMSHR(C,R) )/PM0(C,R);

*World price = import value (in foreign currency / import quantity)
*JT: REGIONAL
 PWM0(C,R)$CMR(C,R)                  = (SAM('ROW',C)*REGIMP(C,R)/EXR0) / QM0(C,R);
 tm0(C,R)$(SAM('ROW',C)*REGIMP(C,R)) = (TAXPAR('IMPTAX',C)*REGTAR(C,R)) / (SAM('ROW',C)*REGIMP(C,R));
 tm(C,R)                             = tm0(C,R);

*Composite supply is the sum of domestic market sales and imports
*(since they are initialized at the same price).
 QQ0(C)$(CD(C) OR CM(C)) = QD0(C) + SUM(R, QM0(C,R)) ;
 PQ0(C)$QQ0(C) = (SAM(C,'TOTAL') - SAM(C,'ROW'))/QQ0(C);
 TQ0(C)$QQ0(C) = TAXPAR('COMTAX',C)/(PQ0(C)*QQ0(C)) ;
 tqbar(C)      = TQ0(C) ;

*The following code works when for any number of sectors providing
*transactions services, as well as for the case when they are not
*in the SAM.

PARAMETERS
 SHCTD(C)  share of comm'y ct in trans services for domestic sales
 SHCTM(C)  share of comm'y ct in trans services for imports
 SHCTE(C)  share of comm'y ct in trans services for exports
  ;

 SHCTD(CT) = SUM(CTD, SAM(CT,CTD)/SAM('TOTAL',CTD)) ;
 SHCTM(CT) = SUM(CTM, SAM(CT,CTM)/SAM('TOTAL',CTM)) ;
 SHCTE(CT) = SUM(CTE, SAM(CT,CTE)/SAM('TOTAL',CTE)) ;

*Transactions input coefficients
 icd(CT,C)$QD0(c)
   = (shctd(ct)*SUM(CTD, SAM(CTD,C))/PQ0(ct)) / QD0(C);

 icm(CT,C)$SUM(R, QM0(C,R))
  = (shctm(ct)*SUM(CTM, SAM(CTM,C))/PQ0(ct)) / SUM(R, QM0(C,R));

 ice(CT,C)$SUM(R, QE0(C,R))
  = (shcte(ct)*SUM(CTE, SAM(CTE,C))/PQ0(ct)) / SUM(R, QE0(C,R));

*Indirect activity tax rate = tax payment / output value
*Tax is here applied to total output value (incl. on-farm cons.)
 tva0(A)$(PVA0(A)*QVA0(A)) = TAXPAR('VATAX',A) / (PVA0(A)*QVA0(A));
 tva(A)        = tva0(A);

*QA is GROSS of tax, so base for ta is as well
 ta0(A)$SAM(A,'TOTAL') = TAXPAR('ACTTAX',A) / (SAM(A,'TOTAL'));
 ta(A)         = ta0(A);

*Yield coefficient
* = quantity produced (including home-consumed output)
*   /activity quantity
 theta(A,C)$PXAC0(A,C)
  = ( (SAM(A,C) + SUM(H, SHRHOME(A,C,H)*SAM(A,H)) ) / PXAC0(A,C) )
                                                              / QA0(A);

*Intermediate input coefficient = input use / output quantity
 QINTA0(A) = SUM(C$PQ0(C), SAM(C,A)  / PQ0(C)) ;

 ica(C,A)$(QINTA0(A)$PQ0(C))
               = SAM(C,A)/PQ0(C) / QINTA0(A) ;

 inta(A)$QA0(A) = QINTA0(A) / QA0(A) ;
 pinta0(A)      = SUM(C, ica(C,A)*PQ0(C)) ;

*CPI weight by comm'y = hhd cons value for comm'y / total hhd cons value
*CPI does not consider on-farm consumption.
 cwts(C)       = SUM(H, SAM(C,H)) / SUM((CP,H), SAM(CP,H));

*Domestic sales price index weight = dom sales value for comm'y
*/ total domestic salues value
*Domestic sales price index does not consider on-farm consumption.
 dwts(C)       = (SUM(A, SAM(A,C)) - (SAM(C,'ROW') -
                  SUM(cte, SAM(cte,C))))/
                  SUM(CP, SUM(A, SAM(A,CP)) - (SAM(CP,'ROW') -
                  SUM(cte, SAM(cte,CP))));

 CWTSCHK       = SUM(C, cwts(C));
 DWTSCHK       = SUM(C, dwts(C));

 CPI0          = SUM(C, cwts(C)*PQ0(C)) ;
 DPI0          = SUM(CD, dwts(CD)*PDS0(CD)) ;

DISPLAY CWTSCHK, DWTSCHK;

*Production and trade block -------------------------

*Compute exponents from elasticites
 rhoq(C)$(CM(C) AND CD(C))  = (1/TRADELAS(C,'SIGMAQ')) - 1;

 rhot(C)$(CE(C) AND CD(C))  = (1/TRADELAS(C,'SIGMAT')) + 1;
 rhova(A)$PRODELAS(A)       = (1/PRODELAS(A)) - 1;
 rhoa(A)$ACES(A)            = (1/PRODELAS2(A)) - 1;

 rhova2(F,A)$SUM(FP, MFA2(F,FP,A)) = (1/PRODELAS3(F,A)) - 1;

*Aggregation of domestic output from different activities

 RHOAC(C)$ELASAC(C) = 1/ELASAC(C) - 1;

 deltaac(A,C)$ (SAM(A,C)$ELASAC(C))
               = (PXAC0(A,C)*QXAC0(A,C)**(1/ELASAC(C)))/
                 SUM(AP, PXAC0(AP,C)*QXAC0(AP,C)**(1/ELASAC(C)));

 alphaac(C)$SUM(A,deltaac(A,C))
               = QX0(C)/
                 (SUM(A$deltaac(A,C), deltaac(A,C) * QXAC0(A,C)
                 **(-RHOAC(C))) )**(-1/RHOAC(C));

PARAMETERS
 WFA(F,A)          wage for factor f in activity a (used for calibration)
 ;

*Demand computations ----

SET
 MFAGG(F,FP,A) directly or indirectly factor F is an agg of FP
*This mapping links aggregate factor F to ALL disaggregate factors
*that are below it in the nest (ie FP).
 ;

* MFAGG(F,FDIS,A)$(MFA2(F,FDIS,A) + SUM(FAGG, MFA2(F,FAGG,A)*MFA2(FAGG,FDIS,A))) = YES;
* MFAGG(F,FDIS,A)$MFA2(F,FDIS,A) = YES;
*The definition of MFAGG could be generalized further.

* MFAGG(F,FLAB,A)$(SUM(FP, FTREE(F,FP,FLAB)) AND SAM(FLAB,A)) = YES;
 MFAGG(F,FP,A)$((SUM(FPP, FTREE(F,FPP,FP)) AND SAM(FP,A)) AND FDIS(FP)) = YES;

DISPLAY AC, FAGG, MFAGG, FDIS, FTREE, FNEST;

*Defining factor employment and supply.
 QF0(F,A)  = QF2BASE(F,A);
*Defining employment for aggregate factors in factor nesting
 QF0(FAGG,A) = SUM(FDIS$MFAGG(FAGG,FDIS,A), QF0(FDIS,A));
*Total factor supply is sum of sectoral factor demand
 QFS0(F)   = SUM(A, QF0(F,A));

*Activity-specific wage is activity labor payment over employment
 WFA(F,A)$SAM(F,A) = SAM(F,A)/QF0(F,A);
*Activity-specific wages for aggregate factors in factor nesting
 WFA(FAGG,A)$QF0(FAGG, A)
  = SUM(FDIS$MFAGG(FAGG,FDIS,A), SAM(FDIS,A))/QF0(FAGG,A);

*Economy-wide wage average is total factor income over employment
 WF0(F)$SUM(A, SAM(F,A)) = SUM(A, SAM(F,A))/SUM(A, QF0(F,A));

 WF0(FAGG)$SUM(A, QF0(FAGG,A))
   = SUM((FDIS,A)$MFAGG(FAGG,FDIS,A), SAM(FDIS,A))
    /SUM(A, QF0(FAGG,A));

*Economy-wide real wage average. Defined as equal to WF in base.
 WFREAL0(F) = WF0(F);

*Factor-specific productivity adjustment parameter
 fprd0(F,A)          = 1;
 fprd(F,A)           = fprd0(F,A);

PARAMETER
  QFS0T(F)       tempory storage for flexible labor supply equation
  WF0T(F)        tempory storage for flexible labor supply equation
;

  QFS0t(F) = QFS0(F);
  WF0t(F)  = WF0(F) ;

DISPLAY
"If the value of WF0 for any factor is very different from one (< 0.1"
"or >10) the user may consider rescaling the initial values for QFBASE"
"or QFSBASE for this factor to get a value of WF0 such that"
"0.1 < WF0 < 10"
 WF0
 ;

*Wage distortion factor
 wfdist0(F,A)$WF0(F) = WFA(F,A)/WF0(F);

*CES activity production function
 deltava(F,A)$MFA1(F,A)
            = (wfdist0(F,A) * WF0(F)
              * (QF0(F,A))**(1+rhova(A)) )
              / SUM(FP$MFA1(FP,A), wfdist0(FP,A) * WF0(FP)*(QF0(FP,A))**(1+rhova(A)));

  alphava0(A)$rhova(A) = QVA0(A)/( SUM(F$MFA1(F,A), deltava(F,A)*QF0(F,A)
               **(-rhova(A))) )**(-1/rhova(A));

 alphava(A) = alphava0(A);

*Lower layer nested factor substitution parameters

 deltava2(F,FP,A)$MFA2(F,FP,A)
   = (wfdist0(FP,A) * WF0(FP) * (QF0(FP,A))**(1+rhova2(F,A)) )
     / SUM(FPP$MFA2(F,FPP,A), wfdist0(FPP,A) * WF0(FPP)*(QF0(FPP,A))**(1+rhova2(F,A)));

  alphava2(F,A)$SUM(FP, MFA2(F,FP,A))
   = QF0(F,A)/( SUM(FP$MFA2(F,FP,A), deltava2(F,FP,A)*QF0(FP,A)
               **(-rhova2(F,A))) )**(-1/rhova2(F,A));

DISPLAY deltava2, alphava2;

*CES top level production function
PARAMETER
  predeltaa(A)  dummy used to define deltaa
  ;

 predeltaa(A)  = 0 ;
 predeltaa(A)$(ACES(A) AND QINTA0(A))
                = (PVA0(A)/PINTA0(A))*(QVA0(A)/QINTA0(A))**(1+rhoa(A)) ;
 deltaa(A)$ACES(A) = predeltaa(A)/(1 + predeltaa(A)) ;
 alphaa(A)$deltaa(A)
                = QA0(A)/((deltaa(A)*QVA0(A)**(-rhoa(A))
                  +(1-deltaa(A))*QINTA0(A)**(-rhoa(A)))**(-1/rhoa(A))) ;

*Intermediate demand
 QINT0(C,A)$PQ0(C) = SAM(C,A) / PQ0(C);

*Transactions demand
 QT0(CT) = ( SUM(CTD, SAM(CT,CTD)) + SUM(CTE, SAM(CT,CTE))
             + SUM(CTM, SAM(CT,CTM)) ) / PQ0(CT) ;

*CET transformation
 deltat0(C,R)$CER(C,R)
   = (PE0(C,R)*(QE0(C,R))**(1-rhot(C)))/( SUM(RP$CER(C,RP), PE0(C,RP)*QE0(C,RP)**(1-rhot(C))) + (PDS0(C)*QD0(C)**(1-rhot(C))) );
 deltat(C,R) =  deltat0(C,R);

 alphat0(C)$(CE(C) AND CD(C))
   = QX0(C)/(SUM(R$CER(C,R), deltat(C,R)*QE0(C,R)**rhot(C))  + ((1-SUM(R$CER(C,R), deltat(C,R)))*QD0(C)**( rhot(C))) )**(1/rhot(C));
 alphat(C) =  alphat0(C);

*Armington aggregation
 deltaq0(C,R)$CMR(C,R) = (PM0(C,R)*(QM0(C,R))**(1+rhoq(C)))/( SUM(RP$CMR(C,RP), PM0(C,RP)*QM0(C,RP)**(1+rhoq(C))) + (PDD0(C)*QD0(C)**(1+rhoq(C))) );
 deltaq(C,R)        = deltaq0(C,R);

 alphaq0(C)$CM(C)
   = QQ0(C)/(SUM(R$CMR(C,R), deltaq(C,R)*QM0(C,R)**(-rhoq(C))) + ((1-SUM(R$CMR(C,R), deltaq(C,R)))*QD0(C)**(-rhoq(C))) )**(-1/rhoq(C));
 alphaq(C)          = alphaq0(C);


*Institution block ------------------------------

*Institutional income
 YI0(INSDNG) = SAM('TOTAL',INSDNG);

*Factor income by factor category
 YF0(F) = SUM(A, SAM(F,A));

*Institution income from factors
 YIF0(INSD,F) = SAM(INSD,F);

*Transfers to RoW from factors
 trnsfr('ROW',F) = SAM('ROW',F)/EXR0;

*Transfers from RoW to institutions
 trnsfr(INSD,'ROW') = SAM(INSD,'ROW')/EXR0;

*Government transfers
 trnsfr(INSD,'GOV') = SAM(INSD,'GOV')/CPI0;

*Factor taxes
 tf0(F)$SAM('TOTAL',F)        = TAXPAR('FACTAX',F)/SAM('TOTAL',F);
 tf(F)         = tf0(F);

*Shares of domestic institutions in factor income (net of factor taxes
*and transfers to RoW).
 shif(INSD,F)$SAM(F,'TOTAL')  = SAM(INSD,F)/(SAM(F,'TOTAL') - TAXPAR('FACTAX',f)
                 - SAM('ROW',F));

 SHIFCHK(F)    = SUM(INSD, shif(INSD,F));

DISPLAY
 SHIFCHK;

*Inter-institution transfers
 TRII0(INSDNG,INSDNGP) = SAM(INSDNG,INSDNGP);

*Share of dom non-gov institution in income of other dom non-gov
*institutions (net of direct taxes and savings).
 shii(INSDNG,INSDNGP)$(SAM('TOTAL',INSDNGP) - TAXPAR('INSTAX',INSDNGP) - SAM('S-I',INSDNGP))
  = SAM(INSDNG,INSDNGP)
   /(SAM('TOTAL',INSDNGP) - TAXPAR('INSTAX',INSDNGP) - SAM('S-I',INSDNGP));

*Scaling factors for savings, sales and direct tax shares
 MPSADJ0      = 0;
 TINSADJ0     = 0;
 TQADJ0       = 0;

*Savings rates
 MPS0(INSDNG)$(SAM('TOTAL',INSDNG) - TAXPAR('INSTAX',INSDNG))
  = SAM('S-I',INSDNG)/(SAM('TOTAL',INSDNG) - TAXPAR('INSTAX',INSDNG));
 mpsbar(INSDNG) = MPS0(INSDNG);

*Direct tax rates
 TINS0(INSDNG)$SAM('TOTAL',INSDNG)
  = TAXPAR('INSTAX',INSDNG) / SAM('TOTAL',INSDNG);
 tinsbar(INSDNG) = TINS0(INSDNG);

*"Point" change in savings, sales and direct tax shares
 DMPS0  = 0;
 DTINS0 = 0;
 DTQ0   = 0;

*Selecting institutions for potential "point" change in savings and tax rates

*If DMPS or MPSADJ is flexible, institutions with a value of 1 for mps01
*change their savings rates.
 mps01(INSDNG)  = 1;

*If DTIMS is flexible, institutions with a value of 1 for tins01 change
*their savings rates.
 tins01(INSDNG) = 1;

*If DTQ is flexible, commodities with a value of 1 for tq01 change
*their sales tax rates.
 tq01(C) = 1;

*Household consumption spending and consumption quantities.
 EH0(H)$SAM(H,'TOTAL')        = SUM(C, SAM(C,H)) + SUM(A, SAM(A,H));
 QH0(C,H)$PQ0(C) = SAM(C,H)/PQ0(C);

*Government indicators
 YG0                = SAM('TOTAL','GOV');
 EG0                = SAM('TOTAL','GOV') - SAM('S-I','GOV');
 QG0(C,GOVF)$(PQ0(C) AND SUM(GOVFP, GOVFSHR(C,GOVFP))) = SAM(C,'GOV')/PQ0(C) * (GOVFSHR(C,GOVF)/SUM(GOVFP, GOVFSHR(C,GOVFP)));

 qbarg0(C,GOVF) = QG0(C,GOVF);
 qbarg(C,GOVF)  = qbarg0(C,GOVF);
 GADJ0(GOVF)    = 1;
 MGADJ0         = 1;
 GSAV0          = SAM('S-I','GOV');

*LES calibration ------------------------------------------

PARAMETERS
 BUDSHRtot(H)
 BUDSHR(C,H)    budget share for marketed commodity c and household h
 BUDSHR2(A,C,H) budget share for home commodity c - act a - hhd h
 BUDSHRCHKtot(H)
 BUDSHRCHK(H)   check that budget shares some to unity
 ELASCHK(H)     check that expenditure elasticities satisfy Engel aggr
 ;

 BUDSHRtot(H)   = (SUM(CP, SAM(CP,H)) + SUM(AP, SAM(AP,H)));
 BUDSHR(C,H)$BUDSHRtot(H)    = SAM(C,H)/ BUDSHRtot(H);

 BUDSHR2(A,C,H)$BUDSHRtot(H) = SAM(A,H)*SHRHOME(A,C,H) /BUDSHRtot(H);

 BUDSHRCHK(H)   = SUM(C, BUDSHR(C,H)) + SUM((A,C), BUDSHR2(A,C,H));

 ELASCHK(H)     = SUM(C, BUDSHR(C,H)*LESELAS1(H,C))
                  + SUM((A,C), BUDSHR2(A,C,H)*LESELAS2(A,C,H));

DISPLAY BUDSHR, BUDSHR2, BUDSHRCHK, LESELAS1, LESELAS2, ELASCHK;

 LESELAS1(H,C)$ELASCHK(H)   = LESELAS1(H,C)/ELASCHK(H);
 LESELAS2(A,C,H)$ELASCHK(H) = LESELAS2(A,C,H)/ELASCHK(H);

 ELASCHK(H)      = SUM(C, BUDSHR(C,H)*LESELAS1(H,C))
                   + SUM((A,C), BUDSHR2(A,C,H)*LESELAS2(A,C,H));

DISPLAY ELASCHK, LESELAS1, LESELAS2;


 betam(C,H)   = BUDSHR(C,H)*LESELAS1(H,C);
 betah(A,C,H) = BUDSHR2(A,C,H)*LESELAS2(A,C,H);

 gammam0(C,H)$BUDSHR(C,H)
     =  ( (SUM(CP, SAM(CP,H)) + SUM(AP, SAM(AP,H))) / PQ0(C) )
                      * ( BUDSHR(C,H) + betam(C,H)/FRISCH(H));

 gammah0(A,C,H)$BUDSHR2(A,C,H)
     =  ( (SUM(CP, SAM(CP,H)) + SUM(AP, SAM(AP,H))) / PXAC0(A,C) )
                      * ( BUDSHR2(A,C,H) + betah(A,C,H)/FRISCH(H));

 gammam(C,H)   =  gammam0(C,H);

 gammah(A,C,H) =  gammah0(A,C,H);

*Checking LES parameters ----------------------------------
PARAMETERS
 SUBSIST(H)  subsistence spending
 FRISCH2(H)  alt. defn of Frisch -- ratio of cons to supernumerary cons
 LESCHK(H)   check on LES parameter definitions (error mssg if error)

 LESELASP(H,*,C,*,CP) price elasticity bt c and cp for h (with c and cp labeled by source)
*LESELASP defines cross-price elasticities when c is different from cp and
*own-price elasticities when c and cp refer to the same commodity.
*Source: Dervis, de Melo and Robinson. 1982. General Equilibrium Models
*for Development Policy. Cambridge University Press, p. 483
 ;
 SUPERNUM(H)  = SUM((A,C), gammah(A,C,H)*PXAC0(A,C))
                + SUM(C, gammam(C,H)*PQ0(C)) ;
 FRISCH2(H)$(EH0(H) - SUPERNUM(H))   = -EH0(H)/(EH0(H) - SUPERNUM(H));
 LESCHK(H)$((ABS(FRISCH(H) - FRISCH2(H)) GT 0.00000001) AND (SUM(A, SAM(A,H))+SUM(C, SAM(C,H)))) = 1/0;

PARAMETER  SUPINCSHR(H);

SUPINCSHR(H)$EH0(H) = SUPERNUM(H)/EH0(H)*100;

DISPLAY "Supernumerary expenditure as a percentage of total household expenditure", FRISCH2, SUPINCSHR, LESCHK;

$ontext
*Cross-price elasticities : COMPUATATION IS TIME CONSUMING (BEST LEFT OUT OF COMPILATION)

 LESELASP(H,'MRK',C,'MRK',CP)$(ORD(C) NE ORD(CP))
   = -LESELAS1(H,C)
     * PQ0(CP)*gammam(CP,H) / (SUM(CPP, SAM(CPP,H)) + SUM(APP, SAM(APP,H)));

 LESELASP(H,A,C,'MRK',CP)$(ORD(C) NE ORD(CP))
   = -LESELAS2(A,C,H)
     * PQ0(CP)*gammam(CP,H) / (SUM(CPP, SAM(CPP,H)) + SUM(APP, SAM(APP,H)));

 LESELASP(H,'MRK',C,A,CP)$(ORD(C) NE ORD(CP))
   = -LESELAS1(H,C)
     * PXAC0(A,CP)*gammah(A,CP,H) / (SUM(CPP, SAM(CPP,H)) + SUM(APP, SAM(APP,H)));

*Own-price elasticities

 LESELASP(H,'MRK',C,'MRK',C)
   = -LESELAS1(H,C)
     *( PQ0(C)*gammam(C,H) / (SUM(CP, SAM(CP,H)) + SUM(AP, SAM(AP,H)))
                                                       - 1/FRISCH(H));

 LESELASP(H,A,C,A,C)
   = -LESELAS2(A,C,H)
     *( PXAC0(A,C)*gammah(A,C,H) / (SUM(CP, SAM(CP,H)) + SUM(AP, SAM(AP,H)))
                                                       - 1/FRISCH(H));

OPTION LESELASP:3:2:2;

DISPLAY
 SUPERNUM, FRISCH, FRISCH2, LESCHK, LESELASP
 ;

$offtext

*System-constraint block -------------------------

*Fixed investment
 qbarinv(c)$CINV(C) = SAM(C,'S-I')/PQ0(C);
 QINV0(C)           = qbarinv(C);
 IADJ0              = 1;

*Stock changes
 qdst0(C)$PQ0(C) = (SAM(C,'S-I')$(NOT CINV(C)) + SAM(C,'DSTK'))/PQ0(C);
 qdst(C)         = qdst0(C);

 FSAV0         = SAM('S-I','ROW')/EXR0;

 TABS0         = SUM((C,H), SAM(C,H)) + SUM((A,H), SAM(A,H))
                 + SUM(C, SAM(C,'GOV')) + SUM(C, SAM(C,'S-I'))
                 + SUM(C, SAM(C,'DSTK'));

 INVSHR0       = SAM('TOTAL','S-I')/TABS0;
 MGOVSHR0      = SUM(C, SAM(C,'GOV'))/TABS0;
 GOVSHR0(GOVF) = SUM(C, SAM(C,'GOV')*GOVFSHR(C,GOVF))/TABS0;

 WALRAS0       = 0;

*--------------------------------------------------------------------------------------------
*5. VARIABLE DECLARATIONS -------------------------------------------------------------------
*--------------------------------------------------------------------------------------------
*This section only includes variables that appear in the model.
*The variables are declared in alphabetical order.

VARIABLES
  ALPHAVAADJ(A)  productivity parameter
  CPI            consumer price index (PQ-based)
  DPI            index for domestic producer prices (PDS-based)
  DMPS           change in marginal propensity to save for selected inst
  DTINS          change in domestic institution tax share
  DTQ            change in sales tax rate
  EG             total current government expenditure
  EH(H)          household consumption expenditure
  EXR            exchange rate
  FSAV           foreign savings
  GADJ(GOVF)     government demand scaling factor
  MGADJ          government demand scaling factor
  GOVSHR(GOVF)   govt consumption share of absorption by function
  MGOVSHR        govt consumption share of absorption
  GSAV           government savings
  GDEFGDP        government deficit as a percentage of GDP
  IADJ           investment scaling factor (for fixed capital formation)
  INVSHR         investment share of absorption
  MPS(INS)       marginal propensity to save for dom non-gov inst ins
  MPSADJ         savings rate scaling factor
  PA(A)          output price of activity a
  PDD(C)         demand price for com'y c produced & sold domestically
  PDS(C)         supply price for com'y c produced & sold domestically
  PE(C,R)        price of exports
  PINTA(A)       price of intermediate aggregate
  PM(C,R)        price of imports
  PQ(C)          price of composite good c
  PVA(A)         value added price
  PWE(C,R)       world price of exports
  PWM(C,R)       world price of imports
  PX(C)          average output price
  PXAC(A,C)      price of commodity c from activity a
  QA(A)          level of domestic activity
  QD(C)          quantity of domestic sales
  QE(C,R)        quantity of exports
  QF(F,A)        quantity demanded of factor f from activity a
  QFS(F)         quantity of factor supply
  QG(C,GOVF)     quantity of government consumption
  QH(C,H)        quantity consumed of marketed commodity c by household h
  QHA(A,C,H)     quantity consumed of home commodity c fr act a by hhd h
  QINT(C,A)      quantity of intermediate demand for c from activity a
  QINTA(A)       quantity of aggregate intermediate input
  QINV(C)        quantity of fixed investment demand
  QM(C,R)        quantity of imports
  QQ(C)          quantity of composite goods supply
  QT(C)          quantity of trade and transport demand for commodity c
  QVA(A)         quantity of aggregate value added
  QVAADJ(A)      adjustment to aggregate value added (used for projections)
  QX(C)          quantity of aggregate marketed commodity output
  QXAC(A,C)      quantity of ouput of commodity c from activity a
  TABS           total absorption
  TINS(INS)      rate of direct tax on domestic institutions ins
  TINSADJ        direct tax scaling factor
  TQ(C)          sales tax rate
  TQADJ          sales tax scaling factor
  TRII(INS,INSP) transfers to dom. inst. insdng from insdngp
  WALRAS         savings-investment imbalance (should be zero)
  WALRASSQR      Walras squared
  WF(F)          economy-wide wage (rent) for factor f
  WFREAL(F)      real wage
  WFDIST(F,A)    factor wage distortion variable
  YF(F)          factor income
  YG             total current government income
  YIF(INS,F)     income of institution ins from factor f
  YI(INS)        income of (domestic non-governmental) institution ins
  ;

*--------------------------------------------------------------------------------------------
*6. VARIABLE DEFINITIONS --------------------------------------------------------------------
*--------------------------------------------------------------------------------------------

*The initial levels of all model variables are defined in this file.
$INCLUDE 1VARINIT.INC

*Optional include file that imposes lower limits for selected variables
*The inclusion of this file may improve solver performance.
*$INCLUDE 1VARLOW.INC

*--------------------------------------------------------------------------------------------
*7. EQUATION DECLARATIONS -------------------------------------------------------------------
*--------------------------------------------------------------------------------------------

EQUATIONS

*Price block ----------------------------------------------
 PMDEF(C,R)     domestic import price
 PEDEF(C,R)     domestic export price
 PDDDEF(C)      dem price for com'y c produced and sold domestically
 PQDEF(C)       value of sales in domestic market
 PXDEF(C)       value of marketed domestic output
 PADEF(A)       output price for activity a
 PINTADEF(A)    price of aggregate intermediate input
 PVADEF(A)      value-added price
 CPIDEF         consumer price index
 DPIDEF         domestic producer price index

*Production and trade block -------------------------------
 CESAGGPRD(A)    CES aggregate prod fn (if CES top nest)
 CESAGGFOC(A)    CES aggregate first-order condition (if CES top nest)
 LEOAGGINT(A)    Leontief aggreg intermed dem (if Leontief top nest)
 LEOAGGVA(A)     Leontief aggreg value-added dem (if Leontief top nest)
 CESVAPRD(A)     CES value-added production function
 QVADEF(A)       sector growth projection or adjustment factor
 CESVAFOC(F,A)   CES value-added first-order condition
 CESVAPRD2(F,A)     lower level VA function producing aggregate factor f
 CESVAFOC2(F,FP,A)  lower level VA first-order condition for producing f from fp
 INTDEM(C,A)     intermediate demand for commodity c from activity a
 COMPRDFN(A,C)   production function for commodity c and activity a
 OUTAGGFN(C)     output aggregation function
 OUTAGGFOC(A,C)  first-order condition for output aggregation function
 CET(C)          CET function
 CET2(C)         domestic sales and exports for outputs without both
 ESUPPLY(C,R)    export supply
 ARMINGTON(C)    composite commodity aggregation function
 COSTMIN(C,R)    first-order condition for composite commodity cost min
 ARMINGTON2(C)   comp supply for com's without both dom. sales and imports
 QTDEM(C)        demand for transactions (trade and transport) services
 LBRSUPPLY(F)    labor supply function
 WFREALEQ        real wage equation
 WFDEF(F)        high level wage determination
 RELWAGEQ(F)       wage convergence between skilled and highly-skilled

*Institution block ----------------------------------------
 YFDEF(F)        factor incomes
 YIFDEF(INS,F)   factor incomes to domestic institutions
 YIDEF(INS)      total incomes of domest non-gov't institutions
 EHDEF(H)        household consumption expenditures
 TRIIDEF(INS,INSP) transfers to inst'on ins from inst'on insp
 HMDEM(C,H)      LES cons demand by hhd h for marketed commodity c
 HADEM(A,C,H)    LES cons demand by hhd h for home commodity c fr act a
 INVDEM(C)       fixed investment demand
 GOVDEM(C,GOVF)  government consumption demand
 EGDEF           total government expenditures
 YGDEF           total government income

*System constraint block ----------------------------------
 COMEQUIL(C)     composite commodity market equilibrium
 FACEQUIL(F)     factor market equilibrium
 CURACCBAL       current account balance (of RoW)
 GOVBAL          government balance
 TINSDEF(INS)    direct tax rate for inst ins
 MPSDEF(INS)     marg prop to save for inst ins
 TQDEF(C)        sales tax adjustment equation
 SAVINVBAL       savings-investment balance
 TABSEQ          total absorption
 INVABEQ         investment share in absorption
 GDABEQ(GOVF)    government consumption share in absorption by function
 GDABEQ2         government consumption share in absorption
 OBJEQ           Objective function
;


*--------------------------------------------------------------------------------------------
*8. EQUATION DEFINITIONS --------------------------------------------------------------------
*--------------------------------------------------------------------------------------------
*Notational convention inside equations:
*Parameters and "invariably" fixed variables are in lower case.
*"Variable" variables are in upper case.

*Price block ----------------------------------------------

 PMDEF(C,R)$CMR(C,R)..  PM(C,R) =E= pwm(C,R)*(1 + tm(C,R))*EXR + SUM(CT, PQ(CT)*icm(CT,C));

 PEDEF(C,R)$CER(C,R)..  PE(C,R) =E= pwe(C,R)*(1 - te(C,R))*EXR - SUM(CT, PQ(CT)*ice(CT,C));

 PDDDEF(C)$CD(C).. PDD(C) =E= PDS(C) + SUM(CT, PQ(CT)*icd(CT,C));

 PQDEF(C)$(CD(C) OR CM(C))..
               PQ(C)*(1 - TQ(C))*QQ(C) =E= PDD(C)*QD(C) + SUM(R, PM(C,R)*QM(C,R));

 PXDEF(C)$CX(C)..  PX(C)*QX(C) =E= PDS(C)*QD(C) + SUM(R, PE(C,R)*QE(C,R));

 PADEF(A)$PVA0(A)..  PA(A) =E= SUM(C, PXAC(A,C)*theta(A,C));

 PINTADEF(A)$PVA0(A).. PINTA(A) =E= SUM(C, PQ(C)*ica(C,A)) ;

 PVADEF(A)$PVA0(A)..   PA(A)*(1-ta(A))*QA(A) =E= PVA(A)*QVA(A) + PINTA(A)*QINTA(A) ;

 CPIDEF..      CPI =E= SUM(C, cwts(C)*PQ(C)) ;

 DPIDEF..      DPI =E= SUM(CD, dwts(CD)*PDS(CD)) ;


*Production and trade block -------------------------------

*CESAGGPRD and CESAGGFOC apply to activities with CES function at
*top of technology nest.

 CESAGGPRD(A)$ACES(A)..
   QA(A) =E= alphaa(A)*(deltaa(A)*QVA(A)**(-rhoa(A))
               + (1-deltaa(A))*QINTA(A)**(-rhoa(A)))**(-1/rhoa(A)) ;

 CESAGGFOC(A)$ACES(A)..
   QVA(A) =E= QINTA(A)*((PINTA(A)/PVA(A))*(deltaa(A)/
                                 (1 - deltaa(A))))**(1/(1+rhoa(A))) ;

*LEOAGGINT and LEOAGGVA apply to activities with Leontief function at
*top of technology nest.

 LEOAGGINT(A)$ALEO(A)..  QINTA(A) =E= inta(A)*QA(A) ;

 LEOAGGVA(A)$ALEO(A)..  QVA(A) =E= iva(A)*QA(A) ;

*CESVAPRD, CESVAFOC, INTDEM apply at the bottom of the technology nest
*(for all activities).

 CESVAPRD(A)$QVA0(A)..
    QVA(A) =E= alphava(A)*ALPHAVAADJ(A)*(SUM(F$MFA1(F,A), deltava(F,A)*(fprd(F,A)*QF(F,A))**(-rhova(A))))**(-1/rhova(A)) ;

*Adjustment factor to QVA (used in fixing sector growth)
 QVADEF(A)$QVA0(A).. QVA(A) =E= QVAADJ(A) * QVA0(A);

 CESVAFOC(F,A)$MFA1(F,A)..
   WF(F)*wfdist(F,A) =E=
   PVA(A)*(1-tva(A)) * QVA(A)*SUM(FP, deltava(FP,A)*(fprd(FP,A)*QF(FP,A))**(-rhova(A))  )**(-1)
   *deltava(F,A)*fprd(F,A)**(-rhova(A))*QF(F,A)**(-rhova(A) - 1);

 CESVAPRD2(F,A)$SUM(FP, MFA2(F,FP,A))..
   QF(F,A) =E= alphava2(F,A)*(SUM(FP$MFA2(F,FP,A), deltava2(F,FP,A)*QF(FP,A)**(-rhova2(F,A))) )**(-1/rhova2(F,A)) ;

 CESVAFOC2(F,FP,A)$MFA2(F,FP,A)..
   WF(FP)*wfdist(FP,A) =E=
   WF(F)*wfdist(F,A) * QF(F,A) * SUM(FPP$MFA2(F,FPP,A), deltava2(F,FPP,A)*QF(FPP,A)**(-rhova2(F,A)) )**(-1)*deltava2(F,FP,A)*QF(FP,A)**(-rhova2(F,A)-1);

 INTDEM(C,A)$ica(C,A).. QINT(C,A) =E= ica(C,A)*QINTA(A);

 COMPRDFN(A,C)$theta(A,C)..
    QXAC(A,C) + SUM(H, QHA(A,C,H)) =E= theta(A,C)*QA(A) ;

 OUTAGGFN(C)$CX(C)..
   QX(C) =E= alphaac(C)*SUM(A, deltaac(A,C)*QXAC(A,C)**(-rhoac(C)))**(-1/rhoac(C));

 OUTAGGFOC(A,C)$deltaac(A,C)..
   PXAC(A,C) =E= PX(C)*QX(C) * SUM(AP, deltaac(AP,C)*QXAC(AP,C)**(-rhoac(C)) )**(-1)*deltaac(A,C)*QXAC(A,C)**(-rhoac(C)-1);

 CET(C)$(CE(C) AND CD(C))..
    QX(C) =E= alphat(C)*(SUM(R, deltat(C,R)*QE(C,R)**rhot(C)) + (1 - SUM(R, deltat(C,R)))*QD(C)**rhot(C))**(1/rhot(C)) ;

 ESUPPLY(C,R)$(CER(C,R) AND CD(C))..
   QE(C,R) =E=  QD(C)*((PE(C,R)/PDS(C))*((1 - SUM(RP, deltat(C,RP)))/deltat(C,R)))**(1/(rhot(C)-1)) ;

 CET2(C)$((CD(C) AND CEN(C)) OR (CE(C) AND CDN(C)))..
   QX(C) =E= QD(C) + SUM(R, QE(C,R));

 ARMINGTON(C)$(CM(C) AND CD(C))..
   QQ(C) =E= alphaq(C)*(SUM(R, deltaq(C,R)*QM(C,R)**(-rhoq(C))) + (1-SUM(R, deltaq(C,R)))*QD(C)**(-rhoq(C)))**(-1/rhoq(C));

 COSTMIN(C,R)$(CD(C) AND CMR(C,R))..
   QM(C,R)/QD(C) =E= (PDD(C)/PM(C,R)*deltaq(C,R)/(1-SUM(RP, deltaq(C,RP))))**(1/(1+rhoq(C)));

 ARMINGTON2(C)$( (CD(C) AND CMN(C)) OR (CM(C) AND CDN(C)) )..
   QQ(C) =E= QD(C) + SUM(R, QM(C,R));

 QTDEM(C)$CT(C)..
  QT(C) =E= SUM(CP, icd(C,CP)*QD(CP)) + SUM((CP,R), icm(C,CP)*QM(CP,R)) + SUM((CP,R), ice(C,CP)*QE(CP,R));

 LBRSUPPLY(F)$(FLS(F) AND FDIS(F))..
  QFS(F) =E= QFS0(F)*[ ([SUM(A, WF(F)*WFDIST(F,A)*QF(F,A))/QFS(F)]/CPI) / (WF0(F)/CPI0)]**(etals(F));

 WFREALEQ(F)$WFREAL0(F).. WFREAL(F) =E= SUM(A, WF(F)*wfdist(F,A)*QF(F,A))/((CPI/CPI0)*SUM(A, QF(F,A))) ;

 WFDEF(F)$SUM((FP,A), MFA2(F,FP,A)).. WF(F) =E= SUM((FP,A)$MFA2(F,FP,A), WFDIST(FP,A)*WF(FP)*QF(FP,A) ) / SUM((FP,A)$MFA2(F,FP,A), QF(FP,A) );

 RELWAGEQ(F)$LREL(F).. WFREAL(F)/SUM(FP$MAPRELW(FP,F), WFREAL(FP)) =E= WFREAL0(F)/SUM(FP$MAPRELW(FP,F), WFREAL0(FP)) + CONVERGE(F);

*Institution block ----------------------------------------

 YFDEF(F)$FDIS(F)..  YF(F) =E= SUM(A, WF(F)*wfdist(F,A)*QF(F,A));

 YIFDEF(INSD,F)$shif(INSD,F)..
  YIF(INSD,F) =E= shif(INSD,F)*((1-tf(f))*YF(F) - trnsfr('ROW',F)*EXR);

 YIDEF(INSDNG)$YI0(INSDNG)..
  YI(INSDNG) =E=
   SUM(F, YIF(INSDNG,F))  + SUM(INSDNGP, TRII(INSDNG,INSDNGP)) + trnsfr(INSDNG,'GOV')*CPI + trnsfr(INSDNG,'ROW')*EXR;

 TRIIDEF(INSDNG,INSDNGP)$(shii(INSDNG,INSDNGP))..
  TRII(INSDNG,INSDNGP) =E= shii(INSDNG,INSDNGP) * (1 - MPS(INSDNGP)) * (1 - TINS(INSDNGP))* YI(INSDNGP);

 EHDEF(H)..
  EH(H) =E= (1 - SUM(INSDNG, shii(INSDNG,H))) * (1 - MPS(H)) * (1 - TINS(H)) * YI(H);

 HMDEM(C,H)$betam(C,H)..
   PQ(C)*QH(C,H) =E= PQ(C)*gammam(C,H) + betam(C,H)*( EH(H) - SUM(CP, PQ(CP)*gammam(CP,H))
                         - SUM((A,CP), PXAC(A,CP)*gammah(A,CP,H))) ;

 HADEM(A,C,H)$betah(A,C,H)..
   PXAC(A,C)*QHA(A,C,H) =E=
     PXAC(A,C)*gammah(A,C,H) + betah(A,C,H)*(EH(H) - SUM(CP, PQ(CP)*gammam(CP,H))
                         - SUM((AP,CP), PXAC(AP,CP)*gammah(AP,CP,H))) ;

 INVDEM(C)$CINV(C)..  QINV(C) =E= IADJ*qbarinv(C);

*GOV
 GOVDEM(C,GOVF)..  QG(C,GOVF) =E= MGADJ*GADJ(GOVF)*qbarg(C,GOVF);

 YGDEF..
   YG =E= SUM(INSDNG, TINS(INSDNG)*YI(INSDNG))
          + SUM(f, tf(F)*YF(F))
          + SUM(A, tva(A)*PVA(A)*QVA(A))
          + SUM(A, ta(A)*PA(A)*QA(A))
          + SUM((CM,R), tm(CM,R)*pwm(CM,R)*QM(CM,R))*EXR
          + SUM((CE,R), te(CE,R)*pwe(CE,R)*QE(CE,R))*EXR
          + SUM(C, TQ(C)*PQ(C)*QQ(C))
          + SUM(F, YIF('GOV',F))
          + trnsfr('GOV','ROW')*EXR;

 EGDEF..
   EG =E= SUM((C,GOVF), PQ(C)*QG(C,GOVF)) + SUM(INSDNG, trnsfr(INSDNG,'GOV'))*CPI;


*System constraint block ----------------------------------

 FACEQUIL(F)..  SUM(A, QF(F,A)) =E= QFS(F);

 COMEQUIL(C)..
   QQ(C) =E= SUM(A, QINT(C,A)) + SUM(H, QH(C,H)) + SUM(GOVF, QG(C,GOVF)) + QINV(C) + qdst(C) + QT(C);

 CURACCBAL..
  SUM((CM,R), pwm(CM,R)*QM(CM,R)) + SUM(F, trnsfr('ROW',F)) =E= SUM((CE,R), pwe(CE,R)*QE(CE,R)) + SUM(INSD, trnsfr(INSD,'ROW')) + FSAV;

 GOVBAL.. YG =E= EG + GSAV;

 TINSDEF(INSDNG)..
  TINS(INSDNG) =E= tinsbar(INSDNG)*(1 + TINSADJ*tins01(INSDNG)) + DTINS*tins01(INSDNG);

 MPSDEF(INSDNG)..
  MPS(INSDNG)  =E= mpsbar(INSDNG)*(1 + MPSADJ*mps01(INSDNG)) + DMPS*mps01(INSDNG);

 TQDEF(C)..
  TQ(C)        =E= tqbar(C)*(1 + TQADJ*tq01(C)) + DTQ*tq01(C);

 SAVINVBAL..
   SUM(INSDNG, MPS(INSDNG) * (1 - TINS(INSDNG)) * YI(INSDNG)) + GSAV + FSAV*EXR =E=
                 SUM(C, PQ(C)*QINV(C)) + SUM(C, PQ(C)*qdst(C)) + WALRAS;

 TABSEQ..
  TABS =E= SUM((C,H), PQ(C)*QH(C,H)) + SUM((A,C,H), PXAC(A,C)*QHA(A,C,H))
                 + SUM((C,GOVF), PQ(C)*QG(C,GOVF)) + SUM(C, PQ(C)*QINV(C)) + SUM(C, PQ(C)*qdst(C));

 INVABEQ.. INVSHR*TABS =E= SUM(C, PQ(C)*QINV(C)) + SUM(C, PQ(C)*qdst(C));

 GDABEQ(GOVF)..  GOVSHR(GOVF)*TABS =E= SUM(C, PQ(C)*QG(C,GOVF));

 GDABEQ2..       MGOVSHR*TABS =E= SUM((C,GOVF), PQ(C)*QG(C,GOVF));

 OBJEQ..   WALRASSQR   =E= WALRAS*WALRAS ;

*--------------------------------------------------------------------------------------------
*9. MODEL DEFINITION ------------------------------------------------------------------------
*--------------------------------------------------------------------------------------------

MODEL STANDCGE  standard CGE model /
*Price block (10)
 PMDEF.PM
 PEDEF.PE
 PQDEF.PQ
 PXDEF.PX
 PDDDEF.PDD
 PADEF.PA
 PINTADEF.PINTA
 PVADEF.PVA
 CPIDEF
 DPIDEF
*Production and trade block (17)
 CESAGGPRD
 CESAGGFOC
 LEOAGGINT
 LEOAGGVA
 CESVAPRD.QVA
 QVADEF
 CESVAFOC
 CESVAPRD2
 CESVAFOC2
 INTDEM.QINT
 COMPRDFN.PXAC
 OUTAGGFN.QX
 OUTAGGFOC.QXAC
 CET
 CET2
 ESUPPLY.QE
 ARMINGTON
 COSTMIN
 ARMINGTON2
 QTDEM.QT
 LBRSUPPLY
 WFREALEQ.WFREAL
 WFDEF.WF
 RELWAGEQ
*Institution block (12)
 YFDEF.YF
 YIFDEF.YIF
 YIDEF.YI
 EHDEF.EH
 TRIIDEF.TRII
 HMDEM.QH
 HADEM.QHA
 EGDEF.EG
 YGDEF.YG
 GOVDEM.QG
 GOVBAL
 INVDEM.QINV
*System-constraint block (9)
 FACEQUIL
 COMEQUIL
 CURACCBAL
 TINSDEF.TINS
 MPSDEF.MPS
 TQDEF.TQ
 SAVINVBAL.WALRAS
 TABSEQ.TABS
 INVABEQ
 GDABEQ
 GDABEQ2
 /
 ;

*--------------------------------------------------------------------------------------------
*10. FIXING VARIABLES NOT IN MODEL AT ZERO --------------------------------------------------
*--------------------------------------------------------------------------------------------

  ALPHAVAADJ.FX(A) = 1;
  PDD.FX(C)$(NOT CD(C)) = 0;
  PDS.FX(C)$(NOT CD(C)) = 0;
  PE.FX(C,R)$(NOT CER(C,R)) = 0;
  PM.FX(C,R)$(NOT CMR(C,R)) = 0;
  PX.FX(C)$(NOT CX(C)) = 0;
  PXAC.FX(A,C)$(NOT SAM(A,C)) = 0;
  PVA.FX(A)$(NOT PVA0(A)) = 0;
  QD.FX(C)$(NOT CD(C)) = 0;
  QE.FX(C,R)$(NOT CER(C,R)) = 0;
  QF.FX(F,A)$(NOT (MFA1(F,A) + SUM(FP, MFA2(FP,F,A)))) = 0;
  QG.FX(C,GOVF)$(NOT SAM(C,'GOV')) = 0;
  QH.FX(C,H)$(NOT SAM(C,H)) = 0;
  QHA.FX(A,C,H)$(NOT BETAH(A,C,H)) = 0;
  QINT.FX(C,A)$(NOT SAM(C,A)) = 0;
  QINV.FX(C)$(NOT CINV(C)) = 0;
  QM.FX(C,R)$(NOT CMR(C,R)) = 0;
  QQ.FX(C)$(NOT (CD(C) OR CM(C))) = 0;
  QT.FX(C)$(NOT CT(C)) = 0;
  QVA.FX(A)$(NOT QVA0(A)) = 0;
  QX.FX(C)$(NOT CX(C)) = 0;
  QXAC.FX(A,C)$(NOT SAM(A,C)) = 0;
  TRII.FX(INSDNG,INSDNGP)$(NOT SAM(INSDNG,INSDNGP)) = 0;
  WFREAL.FX(F)$(NOT WFREAL0(F)) = 0;
  YI.FX(INS)$(NOT INSD(INS)) = 0;
  YIF.FX(INS,F)$((NOT INSD(INS)) OR (NOT SAM(INS,F))) = 0;
  YI.FX(INS)$(NOT YI0(INS)) = 0;


*--------------------------------------------------------------------------------------------
*11. MODEL CLOSURE --------------------------------------------------------------------------
*--------------------------------------------------------------------------------------------

$ontext
In the simulation file, SIM.GMS, the user chooses between
alternative closures. Those choices take precedence over the choices
made in this file.

In the following segment, closures is selected for the base model
solution in this file. The clearing variables for micro and macro
constraints are as follows:

FACEQUIL - WF: for each factor, the economywide wage is the
market-clearing variable in a setting with perfect factor mobility across
activities.

CURACCBAL - EXR: a flexible exchange rate clears the current account of
the RoW.

GOVBAL - GSAV: flexible government savings clears the government
account.

SAVINVBAL - SADJ: the savings rates of domestic institutions are scaled
to generate enough savings to finance exogenous investment quantities
(investment-driven savings).

The CPI is the model numeraire.
$offtext

*Factor markets ----------------

*Disaggregate factors:
 QFS.FX(FDIS)$(NOT LREL(FDIS))  = QFS0(FDIS);
 QFS.LO(F)$(FLS(F) AND FDIS(F)) = -INF;
 QFS.UP(F)$(FLS(F) AND FDIS(F)) = +INF;
 WF.LO(FDIS)        = -inf;
 WF.UP(FDIS)        = +inf;
 WFDIST.FX(FDIS,A)  = WFDIST0(FDIS,A);

*Aggregate factors:
 WF.LO(F)$SUM((FP,A), MFA2(F,FP,A))    = -inf;
 WF.UP(F)$SUM((FP,A), MFA2(F,FP,A))    = +inf;
 QFS.LO(F)$SUM((FP,A), MFA2(F,FP,A)) = -INF;
 QFS.UP(F)$SUM((FP,A), MFA2(F,FP,A)) = +INF;
 WFDIST.LO(F,A)$SUM(FP, MFA2(F,FP,A))  = -INF;
 WFDIST.UP(F,A)$SUM(FP, MFA2(F,FP,A))  = +INF;
 QF.LO(F,A)$SUM(FP, MFA2(F,FP,A))  = -INF;
 QF.UP(F,A)$SUM(FP, MFA2(F,FP,A))  = +INF;

*Current account of RoW ----------

* EXR.FX       = EXR0;
 FSAV.FX      = FSAV0;

*Import and export prices (in FCU) are fixed. A change in model
*specification is required if these prices are to be endogenous.
 PWM.FX(C,R)  = PWM0(C,R) ;
 PWE.FX(C,R)  = PWE0(C,R) ;

*Current government balance ------

* GSAV.FX     = GSAV0 ;
 TINSADJ.FX  = TINSADJ0;
 DTINS.FX    = DTINS0;
 DTQ.FX      = DTQ0;
 TQADJ.FX    = TQADJ0;
 GADJ.FX(GOVF) = GADJ0(GOVF);
 MGADJ.FX    = MGADJ0;
* GOVSHR.FX(GOVF)   = GOVSHR0(GOVF) ;
* MGOVSHR.FX  = MGOVSHR0;

*Savings-investment balance ------

 MPSADJ.FX = MPSADJ0;
 DMPS.FX   = DMPS0;
* IADJ.FX   = IADJ0;
* INVSHR.FX = INVSHR0 ;

*Numeraire price index -----------

 CPI.FX        = CPI0;
* DPI.FX        = DPI0;


*--------------------------------------------------------------------------------------------
*12. DISPLAY OF MODEL PARAMETERS AND VARIABLES ----------------------------------------------
*--------------------------------------------------------------------------------------------

DISPLAY
*All parameters in this file and include files are displayed in
*alphabetical order.

ALPHAA   , ALPHAVA0  , ALPHAAC  , ALPHAQ    , ALPHAT    , ALPHAVA
BETAH    , BETAM     , BUDSHR   , BUDSHR2   , BUDSHRCHK , CPI0
CWTS     , CWTSCHK   , DELTAA   , DELTAAC   , DELTAQ
DELTAT   , DELTAVA   , DPI0     , DMPS0     , DTINS0    , DWTS
DWTSCHK  , EG0       , EH0      , ELASAC    , ELASCHK   , EXR0
FRISCH   , FSAV0     , GADJ0    , MGADJ0    , GAMMAH   , GAMMAM    , GOVSHR0   , MGOVSHR0
GSAV0    , IADJ0     , ICA      , ICD       , ICE       , ICM
INTA     , INVSHR0   , IVA      , LESELAS1  , LESELAS2  , MPS0
MPSADJ0  , MPSBAR    , PA0      , PDD0      , PDS0      , PE0
PINTA0   , PM0       , POP      , PQ0       , PRODELAS  , PRODELAS2
PVA0     , PWE0      , PWM0     , PX0       , PXAC0     , QA0
QBARG    , QBARG0    , QBARINV  , QD0       , QDST      , QDST0
QE0      , QF0       , QF2BASE  , QFBASE    , QFS0      , QFSBASE
QG0      , QH0       , QHA0     , QINT0     , QINTA0    , QINV0
QM0      , QQ0       , QT0      , QVA0      , QX0       , QXAC0
RHOA     , RHOAC     , RHOQ     , RHOT      , RHOVA     , SAM
SAMBALCHK, SHCTD     , SHCTE    , SHCTM     , SHIF      , SHIFCHK
SHII     , SHRHOME   , SUPERNUM , TA        , TA0
TABS0    , TAXPAR    , TE       , TE0       , TF        , TF0
THETA    , TINS0     , TINSADJ0 , TINSBAR   , TM        , TM0
TQ0      , TQ0       , TRADELAS , TRII0     , TRNSFR    , TVA
TVA0     , WALRAS0   , WF0      , WFREAL0   , WFA       , WFDIST0   , YF0
YG0      , YI0       , YIF0
;

*--------------------------------------------------------------------------------------------
*13. SOLUTION STATEMENT ---------------------------------------------------------------------
*--------------------------------------------------------------------------------------------

OPTIONS ITERLIM = 1000, LIMROW = 5, LIMCOL = 5, SOLPRINT=ON,
        MCP=PATH, NLP=CONOPT ;

$ontext
These options are useful for debugging. When checking whether the
initial data represent a solution, set LIMROW to a value greater than
the number of equations and search for three asterisks in the listing
file. SOLPRINT=ON provides a complete listing file. The program also
has a number of display statements, so when running experiments it is
usually not necessary to provide a solution print as well.
$offtext

 STANDCGE.HOLDFIXED   = 1 ;
 STANDCGE.TOLINFREP   = .0001 ;

$ontext
The HOLDFIXED option converts all variables which are fixed (.FX) into
parameters. They are then not solved as part of the model.
The TOLINFREP parameter sets the tolerance for determinining whether
initial values of variables represent a solution of the model
equations. Whether these initial equation values are printed is
determimed by the LIMROW option. Equations which are not satsfied to
the degree TOLINFREP are printed with three asterisks next to their
listing.
$offtext

 SOLVE STANDCGE USING MCP ;

*--------------------------------------------------------------------------------------------
*14. OPTIONAL NLP MODEL DEFINITION AND SOLUTION STATEMENT -----------------------------------
*--------------------------------------------------------------------------------------------

$ontext
Define a model that can be solved using a nonlinear programming (NLP)
solver. The model includes the equation OBJEQ which defines the
variable WALRASSQR, which is the square of the Walras' Law variable,
which must be zero in equilibrium.
$offtext

MODEL NLPCGE  standard CGE model for NLP solver /
*Price block (10)
 PMDEF
 PEDEF
 PQDEF
 PXDEF
 PDDDEF
 PADEF
 PINTADEF
 PVADEF
 CPIDEF
 DPIDEF
*Production and trade block (17)
 CESAGGPRD
 CESAGGFOC
 LEOAGGINT
 LEOAGGVA
 CESVAPRD
 CESVAFOC
 INTDEM
 COMPRDFN
 OUTAGGFN
 OUTAGGFOC
 CET
 CET2
 ESUPPLY
 ARMINGTON
 COSTMIN
 ARMINGTON2
 QTDEM
 LBRSUPPLY
 WFREALEQ
*Institution block (12)
 YFDEF
 YIFDEF
 YIDEF
 EHDEF
 TRIIDEF
 HMDEM
 HADEM
 EGDEF
 YGDEF
 GOVDEM
 GOVBAL
 INVDEM
*System-constraint block (9)
 FACEQUIL
 COMEQUIL
 CURACCBAL
 TINSDEF
 MPSDEF
 SAVINVBAL
 TABSEQ
 INVABEQ
 GDABEQ
 GDABEQ2
 OBJEQ
 /
 ;

 NLPCGE.HOLDFIXED   = 1 ;
 NLPCGE.TOLINFREP   = .0001 ;

* SOLVE NLPCGE MINIMIZING WALRASSQR USING NLP ;

*--------------------------------------------------------------------------------------------
*15. SOLUTION REPORTS -----------------------------------------------------------------------
*--------------------------------------------------------------------------------------------

*Optional include file defining report parameters summarizing economic
*data for the base year.

$INCLUDE 1REPBASE.INC

 STANDCGE.MODELSTAT = 0;
 STANDCGE.SOLVESTAT = 0;
 STANDCGE.NUMREDEF  = 0;

 NLPCGE.MODELSTAT = 0;
 NLPCGE.SOLVESTAT = 0;
 NLPCGE.NUMREDEF  = 0;

*============================================================================================
* pystdcge VALIDATION BLOCK (appended 2 Oct 2026; not part of IFPRI's original code)
*============================================================================================
SET SHK  test shocks / BASE, T1, T2, T3, T4 /
    CLS  closures    / SAV, INV /
    ITEM report items / RGDP, RCONS, EXR, RINV /;
PARAMETER
 RES(CLS,SHK,*,*)  results (levels)
 qbarinvB(C)       base investment demand
 trnsfrB(INS,AC)   base transfers
 pwmB(C,R)         base world import prices
 RGDPV             real GDP at base prices
;
 qbarinvB(C) = qbarinv(C);
 trnsfrB(INS,AC) = trnsfr(INS,AC);
 pwmB(C,R) = PWM.L(C,R);
 OPTION LIMROW = 0, LIMCOL = 0, SOLPRINT = OFF;
 STANDCGE.HOLDFIXED = 1;

LOOP(CLS,
* closure: SAV = saving rates fixed, investment adjusts (IFPRI default here);
*          INV = real investment fixed, household saving rates adjust (enterprise rates fixed, as in pystdcge)
  IF(SAMEAS(CLS,'SAV'),
    MPSADJ.FX = MPSADJ0; IADJ.LO = -INF; IADJ.UP = +INF; mps01(INSDNG) = 1;
  ELSE
    IADJ.FX = IADJ0; MPSADJ.LO = -INF; MPSADJ.UP = +INF; mps01(INSDNG) = 1; mps01(EN) = 0;
  );
  LOOP(SHK,
    PWM.FX(C,R) = pwmB(C,R); qbarinv(C) = qbarinvB(C); trnsfr(INS,AC) = trnsfrB(INS,AC); ALPHAVAADJ.FX(A) = 1;
    IF(SAMEAS(SHK,'T1'), PWM.FX('cchem','row') = 1.10*pwmB('cchem','row'); );
    IF(SAMEAS(SHK,'T2'), qbarinv('ccons') = 0.90*qbarinvB('ccons'); );
    IF(SAMEAS(SHK,'T3'), trnsfr(H,'ROW') = 0.90*trnsfrB(H,'ROW'); );
    IF(SAMEAS(SHK,'T4'), ALPHAVAADJ.FX('aagri') = 1.05; );
    SOLVE STANDCGE USING MCP;
    RES(CLS,SHK,'STATUS','MODEL') = STANDCGE.MODELSTAT;
    RES(CLS,SHK,'STATUS','WALRAS') = WALRAS.L;
    RGDPV = SUM((A,C,H), PXAC0(A,C)*QHA.L(A,C,H)) + SUM((C,H), PQ0(C)*QH.L(C,H)) + SUM((C,GOVF), PQ0(C)*QG.L(C,GOVF)) + SUM(C, PQ0(C)*(QINV.L(C)+qdst(C)))
          + SUM((C,R), PE0(C,R)*QE.L(C,R)) - SUM((C,R), pwmB(C,R)*EXR0*QM.L(C,R));
    RES(CLS,SHK,'MACRO','RGDP') = RGDPV;
    RES(CLS,SHK,'MACRO','RCONS') = SUM((C,H), PQ0(C)*QH.L(C,H)) + SUM((A,C,H), PXAC0(A,C)*QHA.L(A,C,H));
    RES(CLS,SHK,'MACRO','RHOME') = SUM((A,C,H), PXAC0(A,C)*QHA.L(A,C,H));
    RES(CLS,SHK,'MACRO','REXP') = SUM((C,R), QE.L(C,R));
    RES(CLS,SHK,'MACRO','RIMP') = SUM((C,R), QM.L(C,R));
    RES(CLS,SHK,'MACRO','EXR') = EXR.L;
    RES(CLS,SHK,'MACRO','CPI') = CPI.L;
    RES(CLS,SHK,'WF',F) = WF.L(F);
    RES(CLS,SHK,'QA',A) = QA.L(A);
    RES(CLS,SHK,'RCONSH',H) = SUM(C, PQ0(C)*QH.L(C,H)) + SUM((A,C), PXAC0(A,C)*QHA.L(A,C,H));
  );
);

FILE OUTF / ifpri_results.csv /;
OUTF.PC = 5; OUTF.ND = 10;
PUT OUTF 'closure', 'shock', 'group', 'item', 'value' /;
LOOP((CLS,SHK),
  LOOP(ITEM$0, );
);
PARAMETER DUMMY;
LOOP((CLS,SHK),
  PUT CLS.TL, SHK.TL, 'STATUS', 'MODEL', RES(CLS,SHK,'STATUS','MODEL') /;
  PUT CLS.TL, SHK.TL, 'STATUS', 'WALRAS', RES(CLS,SHK,'STATUS','WALRAS') /;
  PUT CLS.TL, SHK.TL, 'MACRO', 'RGDP', RES(CLS,SHK,'MACRO','RGDP') /;
  PUT CLS.TL, SHK.TL, 'MACRO', 'RCONS', RES(CLS,SHK,'MACRO','RCONS') /;
  PUT CLS.TL, SHK.TL, 'MACRO', 'REXP', RES(CLS,SHK,'MACRO','REXP') /;
  PUT CLS.TL, SHK.TL, 'MACRO', 'RIMP', RES(CLS,SHK,'MACRO','RIMP') /;
  PUT CLS.TL, SHK.TL, 'MACRO', 'EXR', RES(CLS,SHK,'MACRO','EXR') /;
  PUT CLS.TL, SHK.TL, 'MACRO', 'RHOME', RES(CLS,SHK,'MACRO','RHOME') /;
  LOOP(F, PUT CLS.TL, SHK.TL, 'WF', F.TL, RES(CLS,SHK,'WF',F) /; );
  LOOP(A, PUT CLS.TL, SHK.TL, 'QA', A.TL, RES(CLS,SHK,'QA',A) /; );
  LOOP(H, PUT CLS.TL, SHK.TL, 'RCONSH', H.TL, RES(CLS,SHK,'RCONSH',H) /; );
);
PUTCLOSE OUTF;
