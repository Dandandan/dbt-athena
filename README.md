## dbt-athena

Warning: this adapter is work in progress, contributions welcome!

### Installation
This plugin can be installed via pip:
```
$ pip install git+https://github.com/Dandandan/dbt-athena.git
```

### Configuring your profile

A dbt profile can be configured to run against Athena using the following configuration:

| Option  | Description                                        | Required?               | Example                  |
|---------|----------------------------------------------------|-------------------------|--------------------------|
| s3_staging_dir  | The location where Athena stores meta info | Required  | s3://bucket/staging |
| database  | Specify the database to build models into | Required  | `awscatalog` |
| schema  | Specify the schema to build models into | Required | `dbt_drew` |
| region_name | Specify in which AWS region it should connect | Required | `eu-west-1` |
| threads    | How many threads dbt should use | Optional(default=`1`) | `8` |
| max_retry_number | Number for retries for exponential backoff | Optional(default=`5`) | `8` |
| max_retry_delay  | Maximum delay for exponential backoff in seconds | Optional(default=`100`) | `8` |


**Example profiles.yml entry:**
```
athena_db:
  target: athena_db
  outputs:
    athena_db:
      type: athena
      database: awscatalog
      schema: dbt_dbanin
      region_name: eu-west-1
      threads: 8
```

### Usage Notes

#### Supported Functionality
Due to the nature of Athena, not all core dbt functionality is supported.
The following features of dbt are not implemented on Athena:
- Archival
- Incremental models


If you are interested in helping to add support for this functionality in dbt on Athena, please [open an issue](https://github.com/Dandandan/dbt-athena/issues/new)!

Known issues:

- Quoting is not supported

### Reporting bugs and contributing code

-   Want to report a bug or request a feature? Let us know on [Slack](http://slack.getdbt.com/), or open [an issue](https://github.com/Dandandan/dbt-athena/issues/new).

## Code of Conduct

Everyone interacting in the dbt project's codebases, issue trackers, chat rooms, and mailing lists is expected to follow the [PyPA Code of Conduct](https://www.pypa.io/en/latest/code-of-conduct/).
