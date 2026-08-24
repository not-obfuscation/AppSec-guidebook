package svc

import (
	"database/sql"
	"fmt"
)

var tables = map[string]bool{"orders": true, "invoices": true}

// ПОДСТАВЛЕННЫЙ ДЕФЕКТ 1: конкатенация в SQL, источник — параметр запроса.
func GetOrder(db *sql.DB, orderID string) (*sql.Rows, error) {
	q := fmt.Sprintf("SELECT id, item FROM orders WHERE id = %s", orderID)
	return db.Query(q)
}

func GetOrderSafe(db *sql.DB, orderID string) (*sql.Rows, error) {
	return db.Query("SELECT id, item FROM orders WHERE id = ?", orderID)
}

// ЧИСТЫЙ КОД, ПОХОЖИЙ НА ДЕФЕКТ: имя таблицы из замкнутого множества.
func CountRows(db *sql.DB, table string) (*sql.Rows, error) {
	if !tables[table] {
		return nil, fmt.Errorf("unknown table")
	}
	return db.Query(fmt.Sprintf("SELECT count(*) FROM %s", table))
}

// ПОДСТАВЛЕННЫЙ ДЕФЕКТ 2: тот же дефект, источник приходит из другого файла.
func RawQuery(db *sql.DB, where string) (*sql.Rows, error) {
	return db.Query("SELECT id FROM orders WHERE " + where)
}
