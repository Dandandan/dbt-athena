
-- - get_catalog
-- - list_relations_without_caching
-- - get_columns_in_relation

{% macro presto_ilike(column, value) -%}
	regexp_like({{ column }}, '(?i)\A{{ value }}\Z')
{%- endmacro %}


{% macro athena__get_columns_in_relation(relation) -%}
  {% call statement('get_columns_in_relation', fetch_result=True) %}
      select
          column_name,
          case when regexp_like(data_type, 'varchar\(\d+\)') then 'varchar'
               else data_type
          end as data_type,
          case when regexp_like(data_type, 'varchar\(\d+\)') then
                  from_base(regexp_extract(data_type, 'varchar\((\d+)\)', 1), 10)
               else NULL
          end as character_maximum_length,
          NULL as numeric_precision,
          NULL as numeric_scale

      from
      {{ relation.information_schema('columns') }}

      where {{ presto_ilike('table_name', relation.identifier) }}
        {% if relation.schema %}
        and {{ presto_ilike('table_schema', relation.schema) }}
        {% endif %}
      order by ordinal_position

  {% endcall %}

  {% set table = load_result('get_columns_in_relation').table %}
  {{ return(sql_convert_columns_in_relation(table)) }}
{% endmacro %}


{% macro athena__list_relations_without_caching(relation) %}
  {% call statement('list_relations_without_caching', fetch_result=True) -%}
    select
      table_catalog as database,
      table_name as name,
      table_schema as schema,
      case when table_type = 'BASE TABLE' then 'table'
           when table_type = 'VIEW' then 'view'
           else table_type
      end as table_type
    from {{ relation.information_schema() }}.tables
    where {{ presto_ilike('table_schema', relation.schema) }}
  {% endcall %}
  {{ return(load_result('list_relations_without_caching').table) }}
{% endmacro %}


{% macro athena__reset_csv_table(model, full_refresh, old_relation) %}
    {{ adapter.drop_relation(old_relation) }}
    {{ return(create_csv_table(model)) }}
{% endmacro %}


{% macro athena__create_table_as(temporary, relation, sql) -%}
  create table
    {{ relation }}
  as (
    -- wrapping to select allows to use "with" statements inside "create table"
    select * from (
        {{ sql }}
    )
  );
{% endmacro %}


{% macro athena__drop_relation(relation) -%}
  {% call statement('drop_relation', auto_begin=False) -%}
    drop {{ relation.type }} if exists {{ relation }}
  {%- endcall %}
{% endmacro %}


{% macro athena__drop_schema(relation) -%}
  {% for relation in adapter.list_relations(relation.database, relation.schema) %}
    {% do drop_relation(relation) %}
  {% endfor %}
  {%- call statement('drop_schema') -%}
    drop schema if exists {{ relation }}
  {% endcall %}
{% endmacro %}

{% macro athena__create_schema(database_name, schema_name) -%}
  {%- call statement('create_schema') -%}
    create schema if not exists {{schema_name}}
  {% endcall %}
{% endmacro %}


{% macro athena__rename_relation(from_relation, to_relation) -%}
  {% call statement('rename_relation') -%}
     alter {{ from_relation.type }} {{ from_relation }} rename to {{ to_relation }}
  {%- endcall %}
{% endmacro %}


{% macro athena__load_csv_rows(model) %}
  {{ return(basic_load_csv_rows(model, 1000)) }}
{% endmacro %}


{% macro athena__list_schemas(database) -%}
  {% call statement('list_schemas', fetch_result=True, auto_begin=False) %}
    select distinct schema_name
    from {{ information_schema_name(database) }}.schemata
  {% endcall %}
  {{ return(load_result('list_schemas').table) }}
{% endmacro %}


{% macro athena__check_schema_exists(information_schema, schema) -%}
  {% call statement('check_schema_exists', fetch_result=True, auto_begin=False) -%}
        select count(*)
        from {{ information_schema }}.schemata
        where {{ presto_ilike('catalog_name', information_schema.database) }}
          and {{ presto_ilike('schema_name', schema) }}
  {%- endcall %}
  {{ return(load_result('check_schema_exists').table) }}
{% endmacro %}

{% macro athena__generate_database_name(custom_database_name=none, node=none) -%}
  {% do return(None) %}
{%- endmacro %}

{% macro athena__information_schema_name(database) -%}
  -- {%- if database -%}
  --   {{ database }}.INFORMATION_SCHEMA
  -- {%- else -%}
    INFORMATION_SCHEMA
  -- {%- endif -%}
{%- endmacro %}
