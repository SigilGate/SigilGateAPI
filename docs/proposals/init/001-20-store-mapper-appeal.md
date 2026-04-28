# 001-20 · Store Mapper: appeal.go

**Файл:** `internal/store/mapper/appeal.go`

---

## Messages: JSON в обе стороны

```go
// domain → etcd
msgBytes, err := json.Marshal(a.Messages)
if err != nil {
    return nil, fmt.Errorf("marshal messages: %w", err)
}
ops = append(ops, port.TxnOp{Key: base + "messages", Value: ptr(string(msgBytes))})

// etcd → domain
var msgs []domain.Message
if r.Messages != "" {
    if err := json.Unmarshal([]byte(r.Messages), &msgs); err != nil {
        return domain.Appeal{}, fmt.Errorf("unmarshal messages: %w", err)
    }
}
```

`json.Marshal` возвращает `[]byte`. Преобразуем в `string` для хранения в etcd. При чтении — обратно.

---

## AdminPubID — *PubId

```go
// etcd → domain
var adminPubID *domain.PubId
if r.AdminPubID != "" {
    n, err := strconv.Atoi(r.AdminPubID)
    if err != nil {
        return domain.Appeal{}, fmt.Errorf("parse admin_pub_id: %w", err)
    }
    p := domain.PubId(n)
    adminPubID = &p
}
```

Три шага: `string` → `int` → `PubId` → `*PubId`. Многословно, но каждый шаг виден явно.
