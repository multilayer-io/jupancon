# jupancon

Database Connectors and SQL magics for Jupyter lab.

(What follows is all still *very* WIP)

### Install

```
pip install jupancon
```
### Configure

Write a `~/.jupycon` (old name, have to fix that) YAML file that looks like so (C&P from my actual config file, but heavily censored for obvious reasons):

```
default: my-redshift-cluster

my-redshift-cluster: 
    type: redshift
    host: XXXXXX.XXXXXX.XXXXXXX.redshift.amazonaws.com
    # explicitly setting redshift port (optional)
    port: 5439
    user: XXXXXXXX
    pass: XXXXXXXX
    dbname: XXXXXX


my-gcp:
    type: bigquery
    project: XXXXX-XXXXX-123456

```

# How to use

### Regular usage

```
from jupancon import query, list_schemas, list_tables

list_schemas()

list_tables()

query("select * from foo")
```

### Magical usage

```
from jupancon import load_magics

load_magics()
```

```
select * from foo
```

```
df = %select * from foo
```

```
%%sql

select * 
from foo
where cond = 1
and whatever
```
