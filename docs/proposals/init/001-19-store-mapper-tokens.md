# 001-19 · Store Mapper: jointoken.go + apitoken.go

**Файлы:** `internal/store/mapper/jointoken.go`, `internal/store/mapper/apitoken.go`

---

## JoinToken — bool-поле

```go
// domain → etcd
{Key: base + "used", Value: ptr(strconv.FormatBool(t.Used))}

// etcd → domain
used, err := strconv.ParseBool(r.Used)
if err != nil {
    return domain.JoinToken{}, fmt.Errorf("parse used: %w", err)
}
```

`strconv.FormatBool` / `strconv.ParseBool` — стандартная пара для `bool ↔ string`.

---

## JoinToken — поля ячейки

При чтении: `CellDomain == ""` означает устаревший токен — возвращаем ошибку:

```go
if r.CellDomain == "" {
    return domain.JoinToken{}, fmt.Errorf("устаревший токен: отсутствует cell_domain")
}
```

`NodeNumber` — `int` в domain, строка в record:

```go
// domain → etcd
{Key: base + "node_number", Value: ptr(strconv.Itoa(t.NodeNumber))}

// etcd → domain
nodeNumber, err := strconv.Atoi(r.NodeNumber)
if err != nil {
    return domain.JoinToken{}, fmt.Errorf("parse node_number: %w", err)
}
```

`AssignedDomain` — строка без преобразования. При записи пишется напрямую, при чтении — обязательна (проверяем `!= ""`).

При записи в etcd — все три поля пишутся всегда (не опциональные):

```go
{Key: base + "cell_domain",     Value: ptr(string(t.CellDomain))},
{Key: base + "node_number",     Value: ptr(strconv.Itoa(t.NodeNumber))},
{Key: base + "assigned_domain", Value: ptr(t.AssignedDomain)},
```

---

## ApiToken — *time.Time для LastUsedAt

```go
// etcd → domain
var lastUsed *time.Time
if r.LastUsedAt != "" {
    t, err := time.Parse(time.RFC3339, r.LastUsedAt)
    if err != nil {
        return domain.ApiToken{}, fmt.Errorf("parse last_used_at: %w", err)
    }
    lastUsed = &t
}
```

Указатель на `time.Time` — редкость, но здесь оправдан: `nil` значит «токен ещё не использовался», нулевое `time.Time{}` — это 1 января 0001 года, что неверно семантически.
