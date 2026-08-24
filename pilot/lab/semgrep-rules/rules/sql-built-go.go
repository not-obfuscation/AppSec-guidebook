package svc

import (
	"database/sql"
	"fmt"
)

var tables = map[string]bool{"orders": true}

func getOrder(db *sql.DB, orderID string) (*sql.Rows, error) {
	// ruleid: sql-built-go
	q := fmt.Sprintf("SELECT id FROM orders WHERE id = %s", orderID)
	return db.Query(q)
}

func getOrderSafe(db *sql.DB, orderID string) (*sql.Rows, error) {
	// ok: sql-built-go
	return db.Query("SELECT id FROM orders WHERE id = ?", orderID)
}

func rawQuery(db *sql.DB, where string) (*sql.Rows, error) {
	// ruleid: sql-built-go
	return db.Query("SELECT id FROM orders WHERE " + where)
}

func listAll(db *sql.DB) (*sql.Rows, error) {
	// ok: sql-built-go
	return db.Query("SELECT id FROM orders")
}
