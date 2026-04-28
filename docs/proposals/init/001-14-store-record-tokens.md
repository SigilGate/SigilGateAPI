# 001-14 · Store Record: jointoken.go + apitoken.go

**Файлы:** `internal/store/record/jointoken.go`, `internal/store/record/apitoken.go`

---

## Тот же паттерн

```go
type JoinTokenRecord struct {
    Token          string
    CreatedAt      string
    ExpiresAt      string
    Used           string // "true" | "false"
    CellDomain     string // "" = устаревший токен
    NodeNumber     string // int как строка; "" = устаревший токен
    AssignedDomain string // "" = устаревший токен
}

type ApiTokenRecord struct {
    TokenID    string
    Name       string
    TokenHash  string
    CreatedAt  string
    LastUsedAt string // "" = никогда не использован
    Active     string // "true" | "false"
}
```

---

## bool → "true" / "false"

etcd хранит строки. `Used bool` в domain → `Used string` в record. Mapper: `strconv.FormatBool(used)` и `strconv.ParseBool(rec.Used)`.

Это единственное место где bool появляется как строка — в остальных сущностях boolean-полей нет.

---

## JoinToken — поля ячейки

`CellDomain`, `NodeNumber`, `AssignedDomain` — обязательны для новых токенов. Mapper возвращает ошибку если `CellDomain == ""` (устаревший токен, выпущенный до Arch 2.0).

`NodeNumber` — хранится как строка. Mapper: `strconv.Atoi(r.NodeNumber)` при чтении.
