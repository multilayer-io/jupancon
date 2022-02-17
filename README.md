# jupancon

Database Connectors and SQL magics for [Jupyter](https://docs.jupyter.org/en/latest/). `jupancon` = Jupyter + Pandas + Connectors.

### Features

- Connector to Redshift
- Connector to Bigquery
- Optional automatic tunnel setting through an SSH Bastion
- Querying capabilities
- IPython kernel magics for querying
- Always returns [Pandas DataFrames](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html)

### Install

```bash
pip install jupancon
```
### Configure

Write a `~/.jupancon/config.yml` YAML file that looks similar to the following C&P from my actual config file (heavily censored for obvious reasons):

```yaml
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


my-redshift-behind-sshbastion:
    type: redshift
    use_bastion: true
    bastion_server: censored.bastion.server.com
    bastion_user: XXXXXX
    bastion_host: XXXXXX.XXXXXX.XXXXXX.redshift.amazonaws.com
    host: censored.main.server.com
    user: XXXXXXXX
    pass: XXXXXXXX
    dbname: XXXXXX



```

# How to use

This library is developed primarily for usage within [Jupyter Lab](https://jupyterlab.readthedocs.io/en/stable/getting_started/overview.html). It's likely to work in Jupyter Notebook and Ipython, but untested and unsupported at this stage. Querying will likely work in regular scripts too, but [it will lose its magic](https://ipython.readthedocs.io/en/stable/interactive/magics.html). 

### Regular usage

```python
from jupancon import query, list_schemas, list_tables

list_schemas()

list_tables()

query("select * from foo")
```

### Magical usage

```python
from jupancon import load_magics

load_magics()
```

```python
select * from foo
```

```python
df = %select * from foo
```

```python
%%sql

select * 
from foo
where cond = 1
and whatever
```

# Development

Current status: Jupancon has enough basic features that it's worth open sourcing, but the documentation is still lacking.

### TODO list

- Complete docs (low level stuff, exhaustive features, maybe sphinx/rdd?)
- Add animated gifs to docs 
- Add query monitoring and cancelling functionality

### Features that aren't worth adding right now

- Autocomplete and autodiscover of databases is possible, but not trivial at all. In addition, I'll like to find a way of not adding any extra configuration. Regardless, not worth it until the TODO list above is tackled. See [this project](https://github.com/jupyter-lsp/jupyterlab-lsp) for a successful example.
- Because of the current architecture of Jupyter Lab, syntax highlighting is not feasible to add (as it was in Jupyter Notebook). This might change in the future. See this [git issue](https://github.com/jupyterlab/jupyterlab/issues/3869) for more details.


### A note about Unit Testing

I would like to publish decent unit testing, but this library is hard to test because all the databases currently queried for it's development are either tests that cost me money or private (my clients') databases. Any ideas on how to write an open source, non exploitable set of unit tests for Redshift or BigQuery are very welcome.

