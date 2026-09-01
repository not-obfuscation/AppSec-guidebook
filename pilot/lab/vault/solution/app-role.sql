-- Эталон: учётка только читает таблицу отчётов.

CREATE ROLE "{{name}}" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';
GRANT SELECT ON report_data TO "{{name}}";
