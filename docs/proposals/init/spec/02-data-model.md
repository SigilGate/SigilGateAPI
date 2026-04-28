# 02. Модель данных

## Источник истины

Детальная схема ключей etcd (field-per-key, namespace, null-конвенции) — в документе:
`migrateToArch_2.0/этап-2-миграция-данных-v2.md`

Этот документ описывает **domain-представление** сущностей — как они выглядят внутри приложения, независимо от формата хранения.

## Namespaces

| Namespace | Назначение | Автор записи |
|-----------|-----------|-------------|
| `/sigilgate/` | Сетевой слой: данные для работы сети. Нет персональных данных. | SigilGateApp |
| `/public/` | Коммуникационный слой: данные пользователей, согласившихся на общение. | SigilGateApp |

Связь между слоями — только через `HashTelegramID` (HMAC-SHA256), эфемерно, в памяти приложения. Явных ссылок нет.

## Семантические типы-идентификаторы

Для выражения смысловых ссылок между сущностями используются **defined types** — отдельные типы над примитивами. Компилятор не позволит передать `DeviceUuid` туда, где ожидается `NodeIp`. Явное приведение обязательно.

```go
type NodeIp     string  // IP-адрес ноды — первичный ключ Node
type UserId     int     // автоинкрементный ID пользователя
type DeviceUuid string  // UUID устройства
type PubId      int     // ID пользователя в коммуникационном слое
type TokenId    string  // UUID API-токена
type AppealId   string  // UUID обращения
type CellDomain string  // FQDN первичный ключ Cell (например, necodate.website)
```

Эти типы используются во всех сущностях вместо голых `string` / `int` там, где значение является ссылкой на другую сущность.

## Сущности

### User (сетевой слой)

```go
type User struct {
    ID             UserId
    Username       string
    Status         Status    // active | inactive | archived
    StatusAt       time.Time
    HashTelegramID *string   // HMAC-SHA256; nil у пользователей без Telegram
    Created        time.Time // UTC
    CoreNodes      []NodeIp  // пул Core-нод пользователя; set-семантика, дубликаты исключаются сервисным слоем
}
```

---

### Device (сетевой слой, вложена под User)

```go
type Device struct {
    UUID     DeviceUuid
    UserID   UserId    // → User.ID
    Name     string    // пользовательское название
    Status   Status    // active | inactive | archived
    StatusAt time.Time
    Created  time.Time // UTC
    CoreNode *NodeIp   // → Node.IP; одна из User.CoreNodes; nil до назначения ноды
}
```

**Инвариант:** `device.CoreNode` входит в `user.CoreNodes` (если не nil). Соблюдается сервисным слоем при назначении.

---

### Node (сетевой слой)

```go
type Node struct {
    IP                NodeIp
    Role              NodeRole    // core | entry | mgmt
    Domain            *string     // FQDN; только у core и entry
    ClientServiceName *string     // gRPC service name Client→Entry; только у entry
    CoreServiceName   *string     // gRPC service name Entry→Core; только у core
    CellDomain        *CellDomain // → Cell.Domain; только у core-нод
    NodeNumber        *int        // порядковый номер в ячейке; только у core-нод
    UUID              *string     // Xray UUID ноды; только у core-нод
    Status            Status      // active | inactive | archived
    StatusAt          time.Time
}
```

> `Node` намеренно не имеет поля `Created`: нода — инфраструктурная единица, дата регистрации операционно не нужна. Для аудита достаточно etcd-истории.

---

### Cell (сетевой слой)

Ячейка привязана к домену первого уровня. Core-ноды получают поддомен `{NodeNumber}.core.{CellDomain}`.

```go
type Cell struct {
    Domain   CellDomain // первичный ключ
    Status   Status     // active | inactive | archived
    StatusAt time.Time
}
```

---

### Route (сетевой слой)

Route — проекция связи `Device.CoreNode` для Entry-подов. Entry делает lookup по UUID устройства без знания `UserID` — это горячий путь при каждом клиентском подключении.

```go
type Route struct {
    UUID     DeviceUuid // → Device.UUID
    CoreIP   NodeIp     // → Device.CoreNode → Node.IP
    Status   Status     // active | archived
    StatusAt time.Time
}
```

**Цепочка lookup Entry-пода:**
```
VLESS UUID → Route.CoreIP → Node.Domain (SNI = "{NodeNumber}.core.{CellDomain}")
```

**Инвариант:** `route.CoreIP == device.CoreNode` для активного устройства. При смене `Device.CoreNode` → `Route.CoreIP` обновляется атомарно в одной транзакции.

---

### PublicUser (коммуникационный слой)

```go
type PublicUser struct {
    PubID          PubId
    Username       string
    HashTelegramID string  // для эфемерной корреляции с сетевым слоем
    Telegram       *string // @username
    Email          *string
}
```

> Начальные данные загружаются через `POST /api/v1/backup/load` (миграция из Arch 1.0).
> API для операционной работы с `PublicUser` — вне текущего scope, будет определён позже.

---

### Message (вложен в Appeal)

```go
type Message struct {
    FromPubID PubId
    Text      string
    Ts        time.Time // UTC
}
```

Хранится как JSON blob в одном etcd-ключе — осознанное исключение из field-per-key (сообщения всегда читаются целиком).

---

### Appeal (коммуникационный слой)

```go
type Appeal struct {
    AppealID   AppealId
    PubID      PubId     // → PublicUser.PubID (автор)
    Subject    string
    Status     Status    // inactive | active | archived
    StatusAt   time.Time
    Created    time.Time // UTC
    AdminPubID *PubId    // → PublicUser.PubID; nil до принятия
    Messages   []Message // JSON blob в etcd (исключение из field-per-key)
}
```

> Создание обращений — вне текущего scope. Существующие данные загружаются через миграцию. Эндпоинт `POST /api/v1/appeals` будет определён позже.

---

### JoinToken

```go
type JoinToken struct {
    Token          string
    CreatedAt      time.Time  // UTC
    ExpiresAt      time.Time  // UTC, TTL 24ч
    Used           bool       // одноразовый: true после использования
    CellDomain     CellDomain // → Cell.Domain; ячейка, для которой выпущен токен
    NodeNumber     int        // присвоенный порядковый номер Core-ноды
    AssignedDomain string     // "{NodeNumber}.core.{CellDomain}"; домен для certbot и Node.Domain
}
```

---

### ApiToken

```go
type ApiToken struct {
    TokenID    TokenId
    Name       string    // метка клиента (telegram-bot, keyholder-bot, ...)
    TokenHash  string    // SHA-256 хеш токена (plaintext не хранится)
    CreatedAt  time.Time
    LastUsedAt *time.Time
    Active     bool
}
```

---

## Перечисления

```go
type Status string

const (
    StatusActive   Status = "active"
    StatusInactive Status = "inactive"
    StatusArchived Status = "archived"
)

type NodeRole string

const (
    NodeRoleCore  NodeRole = "core"
    NodeRoleEntry NodeRole = "entry"
    NodeRoleMgmt  NodeRole = "mgmt"
)
```

`Status` — единый для всех сущностей с жизненным циклом. Допустимые переходы между статусами — ответственность сервисного слоя.

---

## Принципы моделирования

- **Натуральные ключи там, где они стабильны**: `NodeIp` для нод, `DeviceUuid` для устройств и маршрутов.
- **Первичный ключ не дублируется в теле объекта** — он уже в etcd-пути.
- **Defined types для ссылочных полей** — `UserId`, `NodeIp`, `PubId` вместо голых `int` / `string`. Несёт смысл и ловится компилятором.
- **`*T` для необязательных полей** — nil означает «не задано». Пустая строка не используется как sentinel.
- **`[]NodeIp` для `CoreNodes`** — set-семантика; сервисный слой гарантирует отсутствие дубликатов.
- **Route как проекция** — не самостоятельная сущность, а индекс для Entry-подов. Всегда консистентен с `Device.CoreNode`.
- **`Messages` в Appeal — JSON blob** — осознанное исключение из field-per-key: сообщения всегда читаются целиком.
- **Числовые ID — через атомарный счётчик в etcd**: ключ `/sigilgate/counters/user_id` хранит текущий максимум. Инкремент — через `compare_and_swap` (optimistic locking). Подробнее: `spec/03-architecture.md`, раздел «Генерация числовых ID».

## Persistence: Record + Mapper

Между domain и etcd — два уровня:

```
EtcdPort          ← raw key-value: Get, Put, Delete, PrefixScan
    ↕
Record            ← плоский map[string]string полей сущности (все значения — строки)
    ↕ Mapper (чистые функции)
Domain object     ← богатые типы: Status, NodeRole, time.Time, []NodeIp, defined types
```

Mapper знает etcd-пути и преобразует `NodeIp → string` и обратно. Record — промежуточное представление, пригодное для round-trip тестов без I/O.
