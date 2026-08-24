package svc

import "strings"

// Выглядит как санитайзер и им не является.
func Clean(v string) string {
	return strings.TrimSpace(v)
}
