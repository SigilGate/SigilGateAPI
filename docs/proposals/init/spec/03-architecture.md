# 03. Архитектура

## Стиль: функциональное ядро, императивная оболочка

- **Ядро** (`domain/`, `service/`, `store/`) — чистые функции над иммутабельными данными. Нет I/O, нет глобального состояния.
- **Оболочка** (`adapter/`, `api/`) — эффекты на границе: etcd, HTTP, конфиг, логирование.
- **Порты** (`port/`) — Go-интерфейсы, разделяющие ядро и оболочку.

## Структура проекта

```
cmd/
└── sigilgateapp/
    └── main.go              ← точка входа: конфигурация, DI, запуск HTTP-сервера

internal/
├── domain/
│   ├── entities.go          ← User, Device, Node, Route, ...
│   ├── enums.go             ← Status, NodeRole и их константы
│   └── errors.go            ← типизированные ошибки: NotFoundError, AlreadyExistsError, ...
│
├── service/
│   ├── user.go              ← use-cases: Create, GetByID, SetStatus, ...
│   ├── device.go
│   ├── node.go
│   ├── route.go
│   ├── cell.go
│   ├── token.go             ← join-токены
│   ├── rotation.go          ← serviceName ротация
│   ├── appeal.go
│   ├── backup.go            ← dump / load
│   └── apitoken.go
│
├── store/
│   ├── record/              ← плоские struct с string-полями (промежуточный слой)
│   │   ├── user.go
│   │   ├── device.go
│   │   └── ...
│   └── mapper/              ← чистые функции: domain ↔ record ↔ etcd-ключи
│       ├── user.go
│       ├── device.go
│       └── ...
│
├── port/
│   ├── etcd.go              ← interface EtcdPort
│   ├── clock.go             ← interface ClockPort
│   └── random.go            ← interface RandomPort
│
├── adapter/
│   ├── etcd.go              ← реальный etcd клиент (mTLS)
│   ├── inmemory_etcd.go     ← in-memory реализация EtcdPort для тестов
│   ├── clock.go             ← реальные time.Now()
│   └── random.go            ← реальные uuid.New()
│
└── api/
    ├── server.go            ← chi router, middleware registration, /health
    ├── composition.go       ← DI: сборка портов → адаптеров → сервисов → хендлеров
    ├── middleware/
    │   └── auth.go          ← Bearer token проверка
    ├── handler/
    │   ├── users.go
    │   ├── devices.go
    │   ├── nodes.go
    │   ├── routes.go
    │   ├── cells.go
    │   ├── tokens.go
    │   ├── appeals.go
    │   ├── backup.go
    │   └── apitokens.go
    └── dto/                 ← request/response structs с json-тегами
        ├── users.go
        ├── devices.go
        └── ...
```

## Слои и зависимости

```
api/handler/ → service/ → domain/
                       → port/ (interface)
service/ → store/mapper/ → store/record/
adapter/ → port/ (реализует interface)
api/composition.go → adapter/ + service/ (точка сборки)
```

**Правило:** `domain/`, `service/`, `store/` не знают про chi, etcd, HTTP. Адаптеры реализуют порты, а не наоборот.

## Порты

```go
// port/etcd.go
type EtcdPort interface {
    Get(ctx context.Context, key string) (*string, error)
    Put(ctx context.Context, key, value string) error
    Delete(ctx context.Context, key string) error
    PrefixScan(ctx context.Context, prefix string) (map[string]string, error)
    Txn(ctx context.Context, ops []TxnOp) error
    CompareAndSwap(ctx context.Context, key string, expected *string, value string) (bool, error)
}

// port/clock.go
type ClockPort interface {
    Now() time.Time
}

// port/random.go
type RandomPort interface {
    UUID() string
}
```

## Обработка ошибок

Ошибки — значения, не исключения. Типизированные ошибки позволяют handler'у выбрать правильный HTTP-статус:

```go
// domain/errors.go
type NotFoundError struct {
    Resource string
    ID       string
}

type AlreadyExistsError struct {
    Resource string
}

type ValidationError struct {
    Field   string
    Message string
}

type StorageError struct {
    Cause error
}
```

Сервис возвращает `(T, error)`. Handler разбирает тип ошибки:

```go
user, err := svc.GetByID(ctx, id)
var notFound *NotFoundError
switch {
case errors.As(err, &notFound): writeError(w, 404, "not_found", notFound.Error())
case err != nil:                writeError(w, 503, "storage_unavailable", "")
default:                        writeJSON(w, 200, toUserResponse(user))
}
```

Маппинг ошибок → HTTP-статусов:
- `NotFoundError` → 404
- `AlreadyExistsError` → 409
- `ValidationError` → 422
- `StorageError` → 503

## Генерация числовых ID

`UserId` — автоинкрементный `int`. В условиях N реплик необходим атомарный инкремент без гонок.

**Механизм: optimistic locking через `CompareAndSwap`**

Счётчик хранится в etcd: `/sigilgate/counters/user_id`. Аллокация:

1. `Get("/sigilgate/counters/user_id")` → текущее значение `N` (или `nil` при первом запуске)
2. `CompareAndSwap(key, expected=N, value=N+1)` — атомарно: если значение совпадает с прочитанным, записать `N+1`
3. Если CAS вернул `true` → `UserId(N+1)` выделен успешно
4. Если `false` → другая реплика опередила, повторить с шага 1

```go
// store/id_allocator.go
func allocateID(ctx context.Context, counterKey string, etcd port.EtcdPort) (int, error) {
    for range maxRetries {
        current, err := etcd.Get(ctx, counterKey)
        if err != nil {
            return 0, &domain.StorageError{Cause: err}
        }
        nextID, expected := computeNext(current)
        ok, err := etcd.CompareAndSwap(ctx, counterKey, expected, strconv.Itoa(nextID))
        if err != nil {
            return 0, &domain.StorageError{Cause: err}
        }
        if ok {
            return nextID, nil
        }
    }
    return 0, &domain.StorageError{Cause: fmt.Errorf("не удалось выделить ID по ключу %s", counterKey)}
}
```

На практике коллизии редки: запись пользователей — не горячий путь.

## Persistence: Record + Mapper

```
etcd PrefixScan("/sigilgate/users/1/") → map[string]string{"username": "...", "status": "active", ...}
                                          ↓ store/record.UserRecord (промежуточный)
                                          ↓ store/mapper.RecordToUser()
                                          → domain.User{ID: 1, Username: "...", Status: StatusActive, ...}
```

Создание объекта — атомарная транзакция (`Txn`). Обновление одного поля — один `Put`.

```
domain.User → store/record.UserRecord → store/mapper.UserToKeys()
                                       → []TxnOp{Put(k, v), ...}
                                       → EtcdPort.Txn(ops)
```

## Внешний доступ: TLS и домен

API недоступен по голому IP. Единственная точка входа — домен с публичным TLS-сертификатом.

### Схема

```
Клиент (Bot / Web)
    ↓ HTTPS :443, LE-сертификат, SNI = <API_DOMAIN>
┌─────────────────────────────────────────────┐
│ K8s Pod                                     │
│  ├── container: nginx                       │
│  │     TLS termination (LE cert)            │
│  │     ACME http-01 renewal (:80)           │
│  │     proxy_pass → localhost:8000          │
│  └── container: sigilgateapp               │
│        net/http + chi :8000 (lo only)       │
│                                             │
│  Shared volume: /etc/letsencrypt            │
└─────────────────────────────────────────────┘
    ↓ mTLS
HA etcd
```

### Два уровня TLS

| Участок | Сертификат | Назначение |
|---------|-----------|-----------|
| Клиент → nginx | Let's Encrypt (публичный) | Выглядит как обычный HTTPS для DPI |
| nginx → sigilgateapp | Нет (localhost) | Внутри пода, без TLS |
| sigilgateapp → etcd | mTLS (внутренний CA) | Аутентификация в кластере |

## Аутентификация

Bearer token в заголовке `Authorization: Bearer <token>`. Middleware вычисляет `SHA-256(token)` и сверяет с `ApiToken.TokenHash` в etcd. Каждый клиент получает свой токен.

## Конфигурация (env vars)

```
SIGILGATEAPP_ETCD_ENDPOINTS=https://<IP_1>:2379,https://<IP_2>:2379,...
SIGILGATEAPP_ETCD_CA_CERT=/etc/ssl/sigilgate/ca.crt
SIGILGATEAPP_ETCD_CLIENT_CERT=/etc/ssl/sigilgate/client.crt
SIGILGATEAPP_ETCD_CLIENT_KEY=/etc/ssl/sigilgate/client.key
SIGILGATEAPP_HOST=127.0.0.1
SIGILGATEAPP_PORT=8000
SIGILGATEAPP_LOG_LEVEL=info
```

Все env vars обязательны (кроме HOST/PORT/LOG_LEVEL с дефолтами). Приложение завершается с ошибкой при старте, если обязательная переменная отсутствует.
