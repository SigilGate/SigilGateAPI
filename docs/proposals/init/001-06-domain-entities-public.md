# 001-06 · Domain: entities_public.go

**Файл:** `internal/domain/entities_public.go`  
**Сущности:** `PublicUser`, `Message`, `Appeal`, `JoinToken`, `ApiToken`

---

## Паттерн тот же, что в entities.go

Те же правила: exported fields, `*string` для optional, `time.Time` вместо `datetime`.

Короткий пример — `Appeal` с вложенным срезом сообщений:

```go
type Message struct {
    FromPubID PubId
    Text      string
    Ts        time.Time
}

type Appeal struct {
    AppealID   AppealId
    PubID      PubId
    Subject    string
    Status     Status
    StatusAt   time.Time
    Created    time.Time
    AdminPubID *PubId     // nil до принятия
    Messages   []Message  // JSON blob в etcd, []Message в domain
}
```

---

## *PubId — указатель на defined type

`AdminPubID *PubId` — то же, что `*string`, но для типизированного ID. Go позволяет указатель на любой тип, включая defined types. `nil` = администратор не назначен.

---

## Messages: в etcd JSON blob, в domain — срез

В etcd `Appeal.Messages` хранится как один JSON-ключ (исключение из field-per-key). В domain — `[]Message`. Mapper отвечает за `json.Marshal` / `json.Unmarshal` при переходе между слоями.
