# Labour Force Survey employment by industry (compile it yourself)

Job-equivalents in the input-output model (`IOTable.jobs`) need employment by major industry group. Make the file from PSA OpenSTAT (free):

1. PSA OpenSTAT, Labor Force Survey, "Number of Employed Persons by Major Industry Group" (2009 PSIC sections, 19 groups), annual 2025.
2. Save as `LFS_2025_employed_by_major_industry.csv` in this folder, with the columns `group,employed_thousand` (one row per group, the group names exactly as in `io80_to_lfs_group_map.csv`).

The maps `io80_to_lfs_group_map.csv` and `io16_to_lfs_group_map.csv` (included) assign each input-output industry to one group.
