# `sreport.py` : Slurm Usage Report

## Usage Examples

- Use `sacct` data directly (requires `sacct`)

```bash
# print report to the STDOUT:
# Total usage is in CPU-Hours or GPU-Hours (= Billing * DurationHours)
python3 sreport.py -S 2026-03-01 -E 2026-03-31

Group           User            Type            Rate            TotalHours
mbit            murat           cuda-large      0.0077          31.98
mbit            murat           cpu             0.00154         6.46
mbit            murat           cuda-small      0.00385         0.12
# save the sreport.py output (including jobs table from sacct):
mkdir hpc-usage-2026-03-reports
python3 sreport.py -S 2026-03-01 -E 2026-03-31 --output hpc-usage-2026-03-reports
```

- Provide the path to CSV file (accounting data from `sacct`)

```bash
# read the table from the CSV file instead of calling sacct
python3 sreport.py -i ./hpc-usage-2026-03-reports/sacct_2026-03-01_2026-03-31_trunc.csv
```

- Set the `sreport.py` permission to be executable with
`chmod +x sreport.py` (and add it to the PATH) for convenience.

```bash
sreport.py -i hpc-usage-2026-03.csv -o hpc-usage-2026-03-reports
```

## Price Rates

Modify the `PRICE_RATES = {..}` dictionary with matching partition names as keys.
Values must be strings (string representation of a float or int.)

## Generate Job Accounting Table

> Preparing `sacct` jobs table for `sreport.py`

You can prepare your Slurm jobs table on a machine with `sacct` (Slurm) to analyse
it later with `sreport.py`.

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
--user=murat \
--format=User,Account,Partition,JobID,JobName,Start,End,ElapsedRaw,AllocTRES,State \
--starttime=2026-03-01 \
--endtime=2026-03-31 \
| sed 's/,/;/g; s/|/,/g' \
| grep -vE 'CANCELLED|FAILED' \
| tee hpc-usage-2026-03.csv \
| column -t -s ','
```

- `grep` and `column` are optional, for filtering and printing the `sacct` output.
- Save the above into a raw report file (e.g., using `tee` as shown above).
- Use the CSV file with `sreport.py` (does not require `sacct`).

## Development and Testing

- `sreport` is intended to be used with the system Python (tested with Python 3.9.24)
- For development and testing use `uv` to set up an environment and run `sreport.py`

```bash
uv sync
uv run sreport.py -i hpc-usage-2026-03.csv
```
