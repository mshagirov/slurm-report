# Slurm Cluster Usage Queries

## List Users with Their Account

```bash
sacctmgr show user withassoc format=user,defaultaccount -p
```

## Cluster usage

```bash
sreport -T "gres/gpu,cpu" \
        cluster \
        AccountUtilizationByUser \
        -t Hour \
        Start=2026-01-01 # End=2026-02-01
```

- Job's resource allocation for each user and job

```bash
# use -T to truncate start/end times
sacct -X -T -p \
      --user=muratmbit \
      --format=User,Account,Partition,JobID,JobName,Start,End,ElapsedRaw,AllocTRES,State \
      --starttime=2026-03-01 \
      --endtime=2026-03-31 \
| sed 's/,/;/g; s/|/,/g' \
| grep -vE 'CANCELLED|FAILED' \ # do not count failed and cancelled jobs
| column -t -s ',' # optional for displaying on CLI
```

- ElapsedRaw: job's elapsed time in second
- AllocCPUS: Total number of CPUs allocated to the job (equivalent to NCPUS).
- AllocTRES: Trackable resources. Resources allocated to the job/step after the job started running.
- State: job status

Other useful options:

```bash
sacct --truncate ...
```

- `--truncate`: truncate jobs started before the `--starttime` and finished before the end time,

Parsing and preparing reports:

- use `-p` to

```bash
sacct -p --delimiter="; " ...

# to get CSV format
sacct -p ... | sed -e 's/,/:/g' -e 's/|/, /g' > report.csv
```
