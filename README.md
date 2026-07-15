# slurm-report

## Generate Job Accounting Table

- Required fields :
  - User
  - Account
  - Partition
  - Start & End (used to compute duration)
  - AllocTRES (must contain `cpu` and `GRES/gpu` values)
- Get parsable information with `-p`.
- For usage reports for a given period, use `-T` to get truncated Job "start"
and "end" times.

```bash
# use -T to truncate start/end times
sacct -X -T -p \
      --user=murat \ # optional and can be used with --allusers
      --format=User,Account,Partition,JobID,JobName,Start,End,ElapsedRaw,AllocTRES,State \
      --starttime=2026-03-01 \
      --endtime=2026-03-31 \
| sed 's/,/;/g; s/|/,/g' \
| grep -vE 'CANCELLED|FAILED' \ # do not count failed and cancelled jobs
> hpc-usage-2026-03.csv
# | column -t -s ',' # optional for displaying on CLI
```

- Save the above into a raw report file.

## Using `sreport.py`

- Provide the path to CSV file (accounting data above) and save the results to
a directory (optional)

```bash
mkdir hpc-usage-2026-03-reports
python3 sreport.py hpc-usage-2026-03.csv --output hpc-usage-2026-03-reports
```

## Development and Testing

- `sreport` is intended to be used with the system Python (tested with Python 3.9.24)
- For development and testing use `uv` to set up an environment and run `sreport.py`

```bash
uv sync
uv run sreport.py hpc-usage-2026-03.csv
```
