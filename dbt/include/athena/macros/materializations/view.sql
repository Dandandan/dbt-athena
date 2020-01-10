{% materialization view, adapter='athena' -%}
    {{ return(create_or_replace_view(run_outside_transaction_hooks=False)) }}
{%- endmaterialization %}
