# Data sources and licences

Every file in `data/` is listed here with its source and licence. Checksums (SHA-256) are in `SHA256SUMS.txt` and are checked by test D1. Files whose terms do not allow redistribution are **not** included; the folders `raw/io`, `raw/fies` and `raw/lfs` explain how to download them.

## Included

| File | Source | Licence |
|---|---|---|
| `raw/sam/002_IFPRI_SAM_PHL_2023_SAM.csv`, `raw/sam/003_IFPRI_SAM_PHL_2023_POP.csv` | IFPRI (2025), *2023 Social Accounting Matrix for Philippines*, Harvard Dataverse, doi:10.7910/DVN/WQXUQW; data paper: IFPRI (2025), *A Nexus Project SAM*, hdl:10568/176224. ₱ billion; 41 activities, 42 commodities, 5 factors, 10 household groups (rural and urban quintiles); population by group (thousands) | CC BY 4.0 (IFPRI Datasets Terms of Use, s. 4) |
| `raw/sam/002_IFPRI_SAM_PHL_2018_SAM.csv`, `raw/sam/003_IFPRI_SAM_PHL_2018_POP.csv` | IFPRI (2021), *2018 Social Accounting Matrix for the Philippines*, Harvard Dataverse, doi:10.7910/DVN/XSEXEP, version 1; data paper Pradesha (2021), doi:10.2499/p15738coll2.134809. Published in whole billions (balanced by `SAM.balance`) | CC BY 4.0 |
| `processed/IFPRI_SAM_PHL_2023_SAM_petroleum_split.csv` | Adaptation of the 2023 SAM: "chemicals and petroleum" split into refined petroleum and other chemicals using shares from PSA's 2018 240-industry input-output table (`tools/build_sam_petroleum_split.py`; the three shares are stored in `pystdcge/oil.py`) | CC BY 4.0 (adaptation of IFPRI data) |
| `processed/elasticities_ph_v1.csv` | Built by `tools/build_elasticities.py` from Kapuscinski and Warr (1999) and the World Bank MANAGE-WB GTAP 9 template (below) | as its sources |
| `raw/elasticities/Kapuscinski_Warr_1999_Table4_ECM.csv` | Kapuscinski, C. A. and Warr, P. G. (1999), Estimation of Armington elasticities: an application to the Philippines, *Economic Modelling* 16(2): 257-278, Table 4 col. 7 and Table 1; transcribed | published estimates, cited |
| `raw/elasticities/Briones_et_al_2023_Table5_LES_elasticities.csv` | Briones, R. M. et al. (2023), PIDS Discussion Paper 2023-23, Tables 4-5 (LES elasticities of AMPLE-CGE) | published estimates, cited |
| `raw/elasticities/MANAGE-WB_GTAP9_template_comPar.csv`, `..._actPar.csv` | World Bank, MANAGE-WB model, `dat/BridgeFile_GTAP_9_template.xlsx`, sheets comPar and actPar | MIT (MANAGE-WB) |
| `raw/elasticities/USDA_ERS_2005ICP_Philippines_elasticities.csv` | USDA ERS, *International Food Consumption Patterns* (2005 ICP); Muhammad, Seale, Meade and Regmi (2011), Technical Bulletin 1929; Philippines rows | US government work (public domain) |
| `raw/cpi/PSA_CPI_weights_2018base_*.csv` | PSA OpenSTAT tables 0012M4ACP25 (all households) and 0022M4ABIR3 (bottom 30%), CPI weights, 2018 = 100 | PSA Open Data, CC BY |
| `raw/lfs/PSA_OpenSTAT_0141B3FEMP7_LFS_employed_by_highest_grade_RAW.csv` and tidy version | PSA OpenSTAT 0141B3FEMP7, Labor Force Survey, employed persons by highest grade completed, Jan 2023-Jul 2026 | PSA Open Data, CC BY |
| `raw/lfs/io80_to_lfs_group_map.csv`, `raw/lfs/io16_to_lfs_group_map.csv` | Maps from PSA's I-O industries to the LFS major industry groups (2009 PSIC sections), made for this package | MIT |
| `raw/macro/PSA_OpenSTAT_0052B5BPRA1_GVA_by_industry_annual_RAW.csv` and tidy version | PSA OpenSTAT 0052B5BPRA1, GVA by industry, annual, constant 2018 prices | PSA Open Data, CC BY |
| `raw/macro/PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv` | PSA OpenSTAT 0012B5BEXQ1, GDP by expenditure, quarterly | PSA Open Data, CC BY |
| `raw/population/PSA_OpenSTAT_0021A3BPOP1_*.csv` and tidy version | PSA OpenSTAT 0021A3BPOP1, population projections based on the 2020 Census, by age and sex, 2020-2030 | PSA Open Data, CC BY |

Other parameters (depreciation and capital-output ratios from the Penn World Table 11.0; public-capital elasticities from Bom and Ligthart 2014; public investment efficiency from IMF Country Report 19/137; the DBCC growth path) are numbers written in the code with their citations, listed in `docs/parameters.md`.

## Not included (download them yourself)

| What | Why | How |
|---|---|---|
| PSA 2018 Input-Output Tables (80 and 16 industries; 240-industry table and supply-use tables for rebuilding the petroleum split) | PSA's terms for traditional publications do not allow commercial redistribution, which an MIT-licensed repository would permit | `raw/io/README.md` |
| PSA Family Income and Expenditure Survey 2023 public-use file | PSA's terms: for the use of the person who downloaded it only | `raw/fies/README.md` |
| LFS employment by major industry group, 2025 | Compile it yourself from PSA OpenSTAT (free) | `raw/lfs/README.md` |

## IFPRI attribution

*This data was provided by the International Food Policy Research Institute (IFPRI). IFPRI bears no responsibility for the analyses or interpretations of the data presented here.* Please cite the dataset and the data paper above in any publication.
