# Политика приложения «отчёты» — бланк.
# Приложению нужно одно: читать временную учётку из
# database/creds/reporting-app. Всё остальное — лишнее.

path "database/*" {
  capabilities = ["read"]
}
