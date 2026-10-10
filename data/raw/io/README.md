# PSA input-output tables (download them yourself)

The input-output model (`pystdcge.iomodel`) and tests I3-I4 use the Philippine Statistics Authority's **2018 Input-Output Accounts of the Philippines** (released December 2021). They are not included in this repository (`data/DATA_SOURCES.md` explains why).

1. Go to the PSA website, section *Input-Output Tables* (search psa.gov.ph for "2018 Input-Output Tables").
2. Download into this folder, keeping PSA's file names:
   - `80-Industry20Table202018.xlsx` (Table B.1, 80-industry transactions table);
   - `16-Industry20Table202018.xlsx` (Table A.1, 16-industry transactions table);
   - optional, to rebuild the petroleum split (`tools/build_sam_petroleum_split.py`) or recompute the oil import shares: `240-Industry20Table202018.xlsx` and `2018 Supply and Use Tables.xlsx`.
3. From the repository root, run `python data/raw/io/psa_io_to_csv.py`. It copies the tables cell by cell into the CSV layout the package reads (nothing is computed).
4. Run `python -m pytest tests/test_io_and_microsim.py`: the input-output identity tests should now pass.

Check: the Leontief inverse computed from Table B.1 should equal PSA's published Table B.3 to about 1e-8.
