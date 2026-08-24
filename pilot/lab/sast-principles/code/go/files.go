package svc

import (
	"os"
	"path/filepath"
)

// ПОДСТАВЛЕННЫЙ ДЕФЕКТ 4: имя файла складывается с корнем без проверки.
func ReadInvoice(name string) ([]byte, error) {
	return os.ReadFile(filepath.Join("/srv/invoices", name))
}
