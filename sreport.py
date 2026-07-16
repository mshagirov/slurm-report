#!/usr/bin/python3

import argparse
import subprocess
from collections import defaultdict
import csv
from datetime import datetime
from pathlib import Path
import re
import sys

# dict[str] -> str
PRICE_RATES = {
    'cuda-small': '0.00385',
    'cuda-large': '0.0077',
    'cpu': '0.00154'
}

def read_csv(csv_path):
    '''
    Returns: col_names, rows
    '''
    try:
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            col_names = reader.fieldnames
            rows = list(reader)
    except Exception as e:
        print(f"Error occurred when reading\n\t{csv_path}")
        raise e

    return col_names, rows


def write_csv(csv_path, col_names, rows):
    try:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=col_names)
            writer.writeheader()
            writer.writerows(rows)
            f.write("\n")
    except Exception as e:
        print(f"Error occurred when writing\n\t{csv_path}")
        raise e


def row_str2dict(col_names, row_str):
    new_row = {}
    for col,val in zip(col_names, row_str.split(',')):
        new_row[col] = val
    return new_row


def slurm_acct(starttime, endtime):
    """Slurm accounting table for a (truncated) period from 'start' to 'end'"""
    cmd = f"sacct -X -T -p --allusers --format=User,Account,Partition,JobID,JobName,Start,End,ElapsedRaw,AllocTRES,State --starttime={starttime} --endtime={endtime}"

    result = subprocess.run(cmd.split(),
                            capture_output=True,
                            text=True,
                            check=True
                            )

    if result.returncode != 0:
        print(f'Error calling sacct\nEXIT {result.returncode}')
        raise Exception(f'{result.stderr}')
    out = result.stdout.replace(',', ';').replace('|', ',').split('\n')
    col_names =  out[0].split(',')
    rows = list(map(lambda x:row_str2dict(col_names,x), filter(lambda x: len(x)>0, out[1:])))
    return col_names, rows


def write_text(filepath, content):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"Error while writing\n  {filepath}")
        raise e


def fix_billing(rows):
    def fix_alloc_tres(alloc_tres):
        if "gres/gpu" not in alloc_tres:
            return alloc_tres
        gpu_match = re.search(r"gres/gpu=(\d+)", alloc_tres)
        if not gpu_match:
            return alloc_tres
        gpu_val = gpu_match.group(1)
        if "billing=" in alloc_tres:
            return re.sub(r"billing=\d+", f"billing={gpu_val}", alloc_tres) 
        else:
            return f"billing={gpu_val};" + alloc_tres
    for row in rows:
        row['AllocTRES']  = fix_alloc_tres(row['AllocTRES'])


def get_billing_value(alloc_tres):
    """Extract billing value from AllocTRES."""
    match = re.search(r"billing=(\d+)", alloc_tres)
    return int(match.group(1)) if match else 0


def add_job_duration_hours(cols, rows):
    """Adds job duration in hours."""
    col_name = 'DurationHours'
    cols.append(col_name)
    for row in rows:
        duration = datetime.fromisoformat(row['End']) - datetime.fromisoformat(row['Start'])
        duration_hours = duration.total_seconds()/3600
        row[col_name] = f'{duration_hours:.2f}'


def add_price_rate(cols, rows):
    """Add Pricing Rate Per Hour"""
    col_name = 'Rate'
    cols.append(col_name)
    for row in rows:
        partition = row['Partition']
        row[col_name] = PRICE_RATES[partition]


def parse_args(args):
    parser = argparse.ArgumentParser(description="Generate Slurm billing report using `sacct`.")
    parser.add_argument('-i', '--input',
                        help='path to CSV file containing a sacct output.; if provided the input CSV will be used instead of sacct command and "starttime" and "endtime" are ignored')
    parser.add_argument('-o', '--output',
                        help='output path for processed CSV files', default=None)
    parser.add_argument('-S', '--starttime',
                        help='start time of the report period in ISO format for `sacct`; DEFAULT: midnight start of the day 00:00:00')
    parser.add_argument('-E', '--endtime',
                        help='end of the report period in ISO format for `sacct`; DEFAULT: current datetime (now)')
    parser.add_argument('--fixbilling',
                        help='use \'cpu\' and \'gres/gpu\' values for billing CPU and GPU jobs',
                        action='store_true')
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])

    if args.input is None:
        csv_file = Path('sacct_output.csv')
        starttime = args.starttime if args.starttime else datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        endtime = args.endtime if args.endtime else datetime.now().replace(microsecond=0).isoformat()
        cols, rows = slurm_acct(starttime, endtime)
    else:
        csv_file = Path(args.input)
        cols, rows = read_csv(csv_file)

    output_dir = args.output

    if args.fixbilling:
        print('BillingFixing: enabled')
        fix_billing(rows)

    if (cols is None) or (rows is None) or (not cols) or (not rows):
        print('Invalid rows or cols')
        print(cols)
        print(rows)
        return

    add_job_duration_hours(cols, rows)
    # add_price_rate(cols, rows)

    users = defaultdict(lambda: defaultdict(float))
    for row in rows:
        user = row.get("User", "")
        group = row.get("Account", "")
        partition = row.get("Partition", "")
        rate = PRICE_RATES.get(partition, '0')
        multiplier = get_billing_value(row['AllocTRES'])
        users[(group, user)][(partition, rate)] += float(row['DurationHours']) * multiplier


    user_cols = ['Group', 'User', 'Type', 'Rate', 'Total']

    user_rows = []
    for u, ps in users.items():
        for p, dur in ps.items():
            row_str = ','.join([','.join(u), ','.join(p), f'{dur:.2f}'])
            user_rows.append(row_str2dict(user_cols, row_str))

    if output_dir is None:
        print(','.join(user_cols))
        for row in user_rows:
            print(','.join(row.values()))
    else:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            print(f'Directory doesn\'t exist:\n {output_dir}')
            return
        write_csv(output_dir/f"{'report_'+ csv_file.name}", user_cols, user_rows)

        if args.input is None:
            write_csv(output_dir/ csv_file.name, cols, rows)


if __name__ == '__main__':
    main()

