# 001-03 · Domain: enums.go

**Файл:** `internal/domain/enums.go`

---

## Python → Go

```python
class Status(str, Enum):
    ACTIVE   = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
```

```go
type Status string

const (
    StatusActive   Status = "active"
    StatusInactive Status = "inactive"
    StatusArchived Status = "archived"
)
```

---

## Ключевые отличия

**Нет `.value`.** В Python `Status.ACTIVE.value` даёт `"active"`. В Go `StatusActive` уже IS строка — можно передавать напрямую туда, где ожидается `string(status)`.

**Нет итерации.** В Python `list(Status)` даёт все варианты. В Go такого нет из коробки. Для валидации входящих строк — явная функция:

```go
func ParseStatus(s string) (Status, error) {
    switch Status(s) {
    case StatusActive, StatusInactive, StatusArchived:
        return Status(s), nil
    }
    return "", &ValidationError{Field: "status", Message: "неизвестный статус: " + s}
}
```

**`iota` не нужен.** `iota` — для int-перечислений (флаги, битовые маски). Здесь значения — строки, которые хранятся в etcd и передаются через API. Используем строки явно.
