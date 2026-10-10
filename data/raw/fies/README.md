# PSA Family Income and Expenditure Survey 2023 (download it yourself)

`pystdcge.microsim` (poverty and distribution) uses PSA's FIES 2023 public-use file. PSA's terms allow its use only by the person who downloaded it, so it is not included and must never be added to a public repository.

1. Register at the PSA Data Archive (psada.psa.gov.ph) and accept PSA's terms of use.
2. Download the FIES 2023 public-use file (the FIES-LFS 2023 collection includes a household summary file).
3. Save into this folder:
   - `FIES-LFS PUF 2023 Household Sum.csv` (household summary, 163,268 households);
   - `FIES2023_official_poverty_lines_extract.csv`, a CSV with one row per household and the columns `w_regn, w_prov, fsize, toinc, rfact, mem_rfact, urb, npcinc, pline_2023, fline_2023`, extracted from PSA's FIES 2023 Stata file (which includes the official 2023 poverty and food thresholds).
4. Run `python -m pytest tests/test_io_and_microsim.py`: test P1 checks that the baseline reproduces PSA's official count of 17.54 million poor people in 2023.

Cite PSA as the source and do not attempt to identify households.
