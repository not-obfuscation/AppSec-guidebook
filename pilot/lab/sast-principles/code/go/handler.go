package svc

import (
	"database/sql"
	"net/http"
)

func HandleOrder(db *sql.DB, w http.ResponseWriter, r *http.Request) {
	rows, err := GetOrder(db, r.URL.Query().Get("id"))
	if err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}
	defer rows.Close()
}

func HandleSearch(db *sql.DB, w http.ResponseWriter, r *http.Request) {
	rows, err := RawQuery(db, Clean(r.URL.Query().Get("where")))
	if err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}
	defer rows.Close()
}

func HandleExport(w http.ResponseWriter, r *http.Request) {
	out, err := Export(r.URL.Query().Get("fmt"))
	if err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}
	_, _ = w.Write(out)
}

func HandleInvoice(w http.ResponseWriter, r *http.Request) {
	out, err := ReadInvoice(r.URL.Query().Get("name"))
	if err != nil {
		http.Error(w, "not found", http.StatusNotFound)
		return
	}
	_, _ = w.Write(out)
}
