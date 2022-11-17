# jupancon

Database Connectors and SQL magics for [Jupyter](https://docs.jupyter.org/en/latest/). `jupancon` = Jupyter + Pandas + Connectors. 

### Features

- Connector to Redshift
    - Using user/pass
    - Using IAM profile
- Connector to Bigquery (using google profile)
- Connector to Databricks
- Optional automatic tunnel setting through an SSH Bastion
- Querying capabilities
- IPython kernel magics for querying
- Always returns [Pandas DataFrames](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html)
- Some hidden stuff I rather not document just yet so you don't nuke your Warehouse :) Will do when it's safer to use

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


my-redshift-using-iamprofile: 
    type: redshift
    host: XXXXXX.XXXXXX.XXXXXXX.redshift.amazonaws.com
    profile: XXXXXXXXX
    dbname: XXXXXX
    # NOTE: you can choose dbuser and it will be auto-created if it doesn't exist 
    dbuser: XXXXXX
    cluster: XXXXXX


my-gcp:
    type: bigquery
    project: XXXXX-XXXXX-123456

my-databricks:
    type: databricks
    server_hostname: XXXXXX.cloud.databricks.com
    http_path: /sql/XXX/XXXX/XXXXXXXXXX
    # optional
    catalog: XXXXXXX
    token: XXXXXXXXX


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

Jupancon will also pick environment variables (which have preference over the `config.yml`). 

- `JPC_DB_TYPE`: `redshift` or `bigquery` 
- `JPC_HOST`: for example, `XXXXXX.XXXXXX.XXXXXX.redshift.amazonaws.com`
- `JPC_USER`: User name
- `JPC_DB`: Database name
- `JPC_PASS`: Password
- `JPC_USE_BASTION`: `true` or leave blank
- `JPC_BASTION_SERVER`
- `JPC_BASTION_HOST`
- `JPC_PROFILE`: IAM profile (for IAM connection only)
- `JPC_CLUSTER`: Redshift cluster (for IAM connection only) 
- `JPC_DBUSER`: Redshift user (for IAM connection only)

# How to use

This library is developed primarily for usage within [Jupyter Lab](https://jupyterlab.readthedocs.io/en/stable/getting_started/overview.html). It's likely to work in Jupyter Notebook and Ipython, but untested and unsupported at this stage. It also works and is being used in regular scripts, but [it obviously loses its magic](https://ipython.readthedocs.io/en/stable/interactive/magics.html). 

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

```sql
select * from foo
```

```sql
df = %select * from foo
```

```sql
%%sql

select * 
from foo
where cond = 1
and label = 'my nice label'
```

# Development

Current status: Jupancon has enough basic features that it's worth open sourcing, but the documentation is still lacking.

### TODO list

- `list_table("schema")` to detect if schema doesn't exist and return error
- Add query monitoring and cancelling functionality
- Complete docs (low level stuff, exhaustive features, maybe sphinx/rdd?)
- Add animated gifs to docs 


### Features that aren't worth adding right now

- Autocomplete and autodiscover of databases is possible, but not trivial at all. In addition, I'll like to find a way of not adding any extra configuration. Regardless, not worth it until the TODO list above is tackled. See [this project](https://github.com/jupyter-lsp/jupyterlab-lsp) for a successful example.
- Because of the current architecture of Jupyter Lab, syntax highlighting is not feasible to add (as it was in Jupyter Notebook). This might change in the future. See this [git issue](https://github.com/jupyterlab/jupyterlab/issues/3869) for more details.


### A note about Unit Testing

I would like to publish decent unit testing, but this library is hard to test because all the databases currently queried for it's development are either tests that cost me money or private (my clients') databases. Any ideas on how to write an open source, non exploitable set of unit tests for Redshift or BigQuery are very welcome.

