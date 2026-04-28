# 001-07 · Domain: validate.go

**Файл:** `internal/domain/validate.go`

---

## Python → Go

```python
def validate_username(username: str) -> Result[str, ValidationError]:
    if not username.strip():
        return Err(ValidationError("username", "не может быть пустым"))
    return Ok(username.strip())
```

```go
func validateUsername(s string) error {
    s = strings.TrimSpace(s)
    if s == "" {
        return &ValidationError{Field: "username", Message: "не может быть пустым"}
    }
    if len(s) > 32 {
        return &ValidationError{Field: "username", Message: "максимум 32 символа"}
    }
    return nil
}
```

---

## Два отличия

**Возвращаемый тип.** В Python — `Result[str, ValidationError]`. В Go — просто `error`. Типизированная ошибка `*ValidationError` реализует `error`, поэтому её можно вернуть напрямую. Вызывающий разберёт тип через `errors.As`.

**Строчная буква = unexported.** `validateUsername` (с маленькой буквы) — функция видна только внутри пакета `domain`. Её вызывает сервисный слой не напрямую, а через методы сущностей или через вызов из `service/`. Если нужно сделать публичной — `ValidateUsername`.
