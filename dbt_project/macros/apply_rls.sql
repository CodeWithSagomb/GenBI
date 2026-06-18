{% macro apply_rls() %}
  {% set rls_tables = ['fct_sales', 'fct_purchases', 'fct_missed_sales', 'fct_wholesaler_returns'] %}
  {% if this.name in rls_tables %}
    DO $$ BEGIN
      ALTER TABLE {{ this }} ENABLE ROW LEVEL SECURITY;
      DROP POLICY IF EXISTS pharmacy_isolation ON {{ this }};
      CREATE POLICY pharmacy_isolation ON {{ this }}
          USING (pharmacy_id = current_setting('app.current_pharmacy_id', true)::int);
    END $$
  {% else %}
    SELECT 1
  {% endif %}
{% endmacro %}
