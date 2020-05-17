from dbt.adapters.athena.connections import AthenaConnectionManager, AthenaCredentials
from dbt.adapters.athena.impl import AthenaAdapter
from dbt.adapters.base import AdapterPlugin
from dbt.include import athena


AthenaConnectionManager = AthenaConnectionManager


Plugin = AdapterPlugin(
    adapter=AthenaAdapter,
    credentials=AthenaCredentials,
    include_path=athena.PACKAGE_PATH,
)
