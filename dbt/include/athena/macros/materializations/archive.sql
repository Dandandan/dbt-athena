
{% materialization archive, adapter='athena' -%}
  {{ exceptions.raise_not_implemented(
    'archive materialization not implemented for '+adapter.type())
  }}
{% endmaterialization %}
