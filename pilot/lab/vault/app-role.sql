-- Создание учётки для приложения «отчёты» — бланк.
-- Vault подставит {{name}}, {{password}}, {{expiration}}.
-- Учётке нужно читать таблицу отчётов — и ничего больше.

CREATE ROLE "{{name}}" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';
GRANT ALL ON ALL TABLES IN SCHEMA public TO "{{name}}";
