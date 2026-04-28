# 001-16 · Store Mapper: user.go

**Файл:** `internal/store/mapper/user.go`

---

## Python → Go

```python
def domain_to_keys(user: User) -> list[tuple[str, str]]:
    base = f"/sigilgate/users/{user.id}/"
    return [
        (f"{base}username", user.username),
        (f"{base}status",   user.status.value),
        ...
    ]
```

```go
const userPrefix = "/sigilgate/users/"

func UserToKeys(u domain.User) []port.TxnOp {
    base := fmt.Sprintf("%s%d/", userPrefix, u.ID)
    ops := []port.TxnOp{
        {Key: base + "username",  Value: ptr(u.Username)},
        {Key: base + "status",    Value: ptr(string(u.Status))},
        {Key: base + "status_at", Value: ptr(u.StatusAt.Format(time.RFC3339))},
        {Key: base + "created",   Value: ptr(u.Created.Format(time.RFC3339))},
    }
    if u.HashTelegramID != nil {
        ops = append(ops, port.TxnOp{Key: base + "hash_telegram_id", Value: u.HashTelegramID})
    }
    return ops
}
```

`ptr` — вспомогательная функция `func ptr(s string) *string { return &s }`. Нужна потому что `TxnOp.Value *string`, а взять адрес строкового литерала напрямую нельзя.

---

## RecordToUser

```go
func RecordToUser(r record.UserRecord) (domain.User, error) {
    statusAt, err := time.Parse(time.RFC3339, r.StatusAt)
    if err != nil {
        return domain.User{}, fmt.Errorf("parse status_at: %w", err)
    }
    // ...
    var htid *string
    if r.HashTelegramID != "" {
        htid = &r.HashTelegramID
    }
    return domain.User{
        ID:             domain.UserId(id),
        Username:       r.Username,
        Status:         domain.Status(r.Status),
        HashTelegramID: htid,
        // ...
    }, nil
}
```

---

## Round-trip тест

```go
func TestUserRoundTrip(t *testing.T) {
    original := domain.User{ID: 1, Username: "alice", Status: domain.StatusActive, ...}
    keys     := UserToKeys(original)
    rec      := keysToRecord(keys) // вспомогательная функция теста
    restored, err := RecordToUser(rec)
    require.NoError(t, err)
    assert.Equal(t, original, restored)
}
```

Это главный тест mapper'а — он ловит ошибки сериализации до того, как они дойдут до etcd.
