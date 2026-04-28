# 001-15 · Store Record: appeal.go

**Файл:** `internal/store/record/appeal.go`

---

```go
type AppealRecord struct {
    AppealID   string
    PubID      string
    Subject    string
    Status     string
    StatusAt   string
    Created    string
    AdminPubID string   // "" = не назначен
    Messages   string   // JSON blob: "[{...}, {...}]"
}
```

---

## Messages — единственное исключение

Все остальные record'ы хранят скалярные строки. `Messages` — JSON-строка целого массива. Mapper делает `json.Unmarshal([]byte(rec.Messages), &msgs)` при переходе в domain.

Это осознанное исключение из field-per-key: сообщения обращения всегда читаются целиком, разбивать их по ключам нет смысла.
