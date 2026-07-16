# slurm-report

## Using `sreport.py`

- Use `sacct` data directly (requires `sacct`)

```bash
# print report to the STDOUT
python3 sreport.py -S 2026-03-01 -E 2026-03-31
# to save the sacct and sreport output specify a directory with --output
python3 sreport.py -S 2026-03-01 -E 2026-03-31 --output hpc-usage-2026-03-reports
```

- Provide the path to CSV file (accounting data from `sacct`) and save the results
to a directory (optional)

```bash
mkdir hpc-usage-2026-03-reports
python3 sreport.py --input hpc-usage-2026-03.csv --output hpc-usage-2026-03-reports
```

- Set the `sreport.py` permission to be executable with
`chmod +x sreport.py` (and add it to the PATH) for convenience.

```bash
sreport.py -i hpc-usage-2026-03.csv -o hpc-usage-2026-03-reports
```

## Generate Job Accounting Table

> Optional as `sacct` can be called from `sreport.py`

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
> hpc-usage-2026-03.csv # write the table to a file
# | column -t -s ',' # optional for displaying on CLI
```

- Save the above into a raw report file.

## Price Rates

Modify the `PRICE_RATES = {..}` dictionary with matching partition names as keys.
Values must be strings (string representation of a float or int.)

## Development and Testing

- `sreport` is intended to be used with the system Python (tested with Python 3.9.24)
- For development and testing use `uv` to set up an environment and run `sreport.py`

```bash
uv sync
uv run sreport.py -i hpc-usage-2026-03.csv
```
