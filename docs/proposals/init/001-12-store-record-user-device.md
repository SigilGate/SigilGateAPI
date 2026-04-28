# 001-12 · Store Record: user.go + device.go

**Файлы:** `internal/store/record/user.go`, `internal/store/record/device.go`

---

## Что такое Record

Record — промежуточный слой между etcd (сырые строки) и domain (богатые типы). Все поля — строки, потому что etcd хранит только `string`.

## Python → Go

```python
@dataclass(frozen=True)
class UserRecord:
    username: str | None
    status: str | None
    status_at: str | None
    hash_telegram_id: str | None
    created: str | None
```

```go
type UserRecord struct {
    Username       string
    Status         string
    StatusAt       string
    HashTelegramID string // пустая строка = не задано
    Created        string
}
```

---

## string, не *string

В domain `HashTelegramID *string` — потому что нулевое значение `""` неотличимо от "задана пустая строка". В record это не проблема: пустая строка из etcd означает «ключ отсутствовал» — mapper знает об этом и преобразует `""` в `nil` при переходе в domain.

---

## CoreNodes — отдельно

`User.CoreNodes []NodeIp` не попадает в `UserRecord` — это отдельный `PrefixScan` по ключам `/sigilgate/users/{id}/core_nodes/`. Mapper собирает их сам, record хранит только скалярные поля.
