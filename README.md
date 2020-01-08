## dbt-presto ([docs](https://docs.getdbt.com/docs/profile-presto#section-required-configuration))

### Installation
This plugin can be installed via pip:
```
$ pip install dbt-presto
```

### Configuring your profile

A dbt profile can be configured to run against Presto using the following configuration:

| Option  | Description                                        | Required?               | Example                  |
|---------|----------------------------------------------------|-------------------------|--------------------------|
| s3_staging_dir  | The location where Athena stores meta info | Required  | s3://bucket/staging |
| database  | Specify the database to build models into | Required  | `analytics` |
| schema  | Specify the schema to build models into | Required | `dbt_drew` |
| region_name | Specify in which AWS region it should connect | Required | `eu-west-1` |
| threads    | How many threads dbt should use | Optional(default=`1`) | `8` |


**Example profiles.yml entry:**
```
my-athena-db:
  target: awscatalog
  outputs:
    awscatalog:
      type: athena
      database: awscatalog
      schema: dbt_dbanin
      region_name: eu-west-1
      threads: 8
```

### Usage Notes

#### Supported Functionality
Due to the nature of Athena, not all core dbt functionality is supported.
The following features of dbt are not implemented on Presto:
- Archival
- Incremental models


If you are interested in helping to add support for this functionality in dbt on Presto, please [open an issue](https://github.com/fishtown-analytics/dbt-athena/issues/new)!

#### Required configuration
<!-- dbt fundamentally works by dropping and creating tables and views in databases.
As such, the following Presto configs must be set for dbt to work properly on Presto:

```
hive.metastore-cache-ttl=0s
hive.metastore-refresh-interval = 5s
hive.allow-drop-table=true
hive.allow-rename-table=true
``` -->


### Reporting bugs and contributing code

-   Want to report a bug or request a feature? Let us know on [Slack](http://slack.getdbt.com/), or open [an issue](https://github.com/fishtown-analytics/dbt-athena/issues/new).

## Code of Conduct

Everyone interacting in the dbt project's codebases, issue trackers, chat rooms, and mailing lists is expected to follow the [PyPA Code of Conduct](https://www.pypa.io/en/latest/code-of-conduct/).
