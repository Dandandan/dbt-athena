from dataclasses import dataclass

from dbt.adapters.base.relation import BaseRelation, Policy


@dataclass
class AthenaQuotePolicy(Policy):
    database: bool = False
    schema: bool = False
    identifier: bool = False


@dataclass
class AthenaIncludePolicy(Policy):
    database: bool = False
    schema: bool = True
    identifier: bool = True


@dataclass(frozen=True, eq=False, repr=False)
class AthenaRelation(BaseRelation):
    quote_character: str = ""
    include_policy: Policy = AthenaIncludePolicy()
    quote_policy: Policy = AthenaQuotePolicy()
    sql_before_create: str = ""
