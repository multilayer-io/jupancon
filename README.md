# jupancon

Database Connectors and SQL magics for Jupyter lab.

(What follows is all still WIP)

### Install

`pip install jupancon`

### Configure

write a `~/.jupancon` YAML file

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
