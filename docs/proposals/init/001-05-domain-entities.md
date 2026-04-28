# 001-05 · Domain: entities.go

**Файл:** `internal/domain/entities.go`  
**Сущности:** `User`, `Device`, `Node`, `Route`, `Cell`, `JoinToken`

---

## Python → Go

```python
@dataclass(frozen=True)
class User:
    id: UserId
    username: str
    status: Status
    core_nodes: frozenset[NodeIp]
    hash_telegram_id: str | None
    created: datetime
```

```go
type User struct {
    ID             UserId
    Username       string
    Status         Status
    StatusAt       time.Time
    CoreNodes      []NodeIp
    HashTelegramID *string
    Created        time.Time
}
```

---

## frozen=True → конвенция

В Go нет встроенной заморозки. `User` — обычный struct, поля публичны. Иммутабельность — конвенция: функции сервисного слоя не изменяют переданный объект, а возвращают новый.

```go
// правильно: возвращаем изменённую копию
func withStatus(u User, s Status, at time.Time) User {
    u.Status   = s
    u.StatusAt = at
    return u   // u передан по значению, оригинал не тронут
}
```

Передача struct по значению (не указатель) — естественная иммутабельность в Go.

---

## str | None → *string

```python
hash_telegram_id: str | None
```

```go
HashTelegramID *string   // nil = не задано
```

Указатель как optional — идиоматично в Go. Нулевое значение `string` это `""`, что неотличимо от "задано пустой строкой" — поэтому `*string`.

---

## frozenset[NodeIp] → []NodeIp

```python
core_nodes: frozenset[NodeIp]
```

```go
CoreNodes []NodeIp
```

Set-семантика (отсутствие дубликатов) обеспечивается сервисным слоем при записи. В domain — просто срез. Порядок элементов не гарантирован и не важен.

---

## Node — новые поля (Arch 2.0)

```python
@dataclass(frozen=True)
class Node:
    ip: NodeIp
    role: NodeRole
    status: Status
    status_at: datetime
    domain: str | None = None
    cell_domain: CellDomain | None = None
    node_number: int | None = None
    uuid: str | None = None
    client_service_name: str | None = None
    core_service_name: str | None = None
```

```go
type Node struct {
    IP                NodeIp
    Role              NodeRole
    Domain            *string
    ClientServiceName *string
    CoreServiceName   *string
    CellDomain        *CellDomain // только у core-нод
    NodeNumber        *int        // только у core-нод
    UUID              *string     // Xray UUID; только у core-нод
    Status            Status
    StatusAt          time.Time
}
```

`CellDomain`, `NodeNumber`, `UUID` — опциональны (`*T`), заполняются только у `role == core`.

---

## JoinToken — поля ячейки

```python
@dataclass(frozen=True)
class JoinToken:
    token: str
    created_at: datetime
    expires_at: datetime
    used: bool
    cell_domain: str
    node_number: int
    assigned_domain: str
```

```go
type JoinToken struct {
    Token          string
    CreatedAt      time.Time
    ExpiresAt      time.Time
    Used           bool
    CellDomain     CellDomain
    NodeNumber     int
    AssignedDomain string // "{NodeNumber}.core.{CellDomain}"
}
```

Все три поля обязательны — токен без `CellDomain` считается устаревшим.

---

## Cell

```go
type Cell struct {
    Domain   CellDomain
    Status   Status
    StatusAt time.Time
}
```
