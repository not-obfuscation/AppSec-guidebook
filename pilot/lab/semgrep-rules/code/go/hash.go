package svc

import (
	"crypto/md5"
	"encoding/hex"
	"strings"
)

// ЧИСТЫЙ КОД, ПОХОЖИЙ НА ДЕФЕКТ: md5 как быстрая свёртка ключа кэша.
func CacheKey(parts []string) string {
	sum := md5.Sum([]byte(strings.Join(parts, "|")))
	return hex.EncodeToString(sum[:])
}
