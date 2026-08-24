package svc

import "os/exec"

// ПОДСТАВЛЕННЫЙ ДЕФЕКТ 3: аргумент внешней команды приходит из запроса.
func Export(format string) ([]byte, error) {
	return exec.Command("/usr/bin/env", "tr", ",", format).Output()
}
