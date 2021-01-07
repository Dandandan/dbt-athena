## dbt-athena

## Note: this repository is not actively maintained. You can find a newer version of the adapter with Athena Engine 2 support, seeds and more in the following repository:
## https://github.com/Tomme/dbt-athena/

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
| schema  | Specify the schema (athena database) to build models into | Required | `dev` |
| database  | Data catalog | Required | `awsdatacatalog` |
| region_name | Specify in which AWS region it should connect | Required | `eu-west-1` |
| threads    | How many threads dbt should use | Optional(default=`1`) | `8` |
| max_retry_number | Number for retries for exponential backoff | Optional(default=`5`) | `8` |
| max_retry_delay  | Maximum delay for exponential backoff in seconds | Optional(default=`100`) | `8` |


**Example profiles.yml entry:**
```
athena:
  target: athena
  outputs:
    athena:
      type: athena
      database: awsdatacatalog
      schema: dev
      region_name: eu-west-1
      threads: 8
      s3_staging_dir: s3://athena-staging-bucket/
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

### Running the tests

#### Unit tests

1. Install tox:

  ```bash
  pip install tox
  ```

2. Run unit tests:

  ```bash
  tox -e unit
  ```

#### Integration tests

At this time, an AWS account is not provided in order to run the tests in CI. We kindly ask contributors/reviewers to use their own AWS accounts in order to test contributions.

You can also reach out in the [Slack](http://slack.getdbt.com/) `#athena` channel for someone to run the tests for you.

Steps:

1. Clone the [dbt-integration-tests](https://github.com/fishtown-analytics/dbt-integration-tests) repository

  ```bash
  git clone --branch athena-support https://github.com/EarnestResearch/dbt-integration-tests.git
  ```

2. Run the tests:

  _Additionally, you might need to set the `AWS_PROFILE` environment variable if you use another value than "default" (for example if you connect to multiple AWS accounts or assume different IAM roles)_

  ```bash
  AWS_DEFAULT_REGION=us-west-2 ATHENA_S3_STAGING_DIR=s3://dbt-athena-integration-tests/tests/ DBT_PROFILES_DIR=$(pwd)/test/integration/ tox -e integration-athena
  ```

## Code of Conduct

Everyone interacting in the dbt project's codebases, issue trackers, chat rooms, and mailing lists is expected to follow the [PyPA Code of Conduct](https://www.pypa.io/en/latest/code-of-conduct/).
