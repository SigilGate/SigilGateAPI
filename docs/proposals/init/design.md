# Design: SigilGateApp (Go)

## Принципы планирования

- Каждый Stage — законченный вертикальный срез: модели + логика + тесты.
- Каждый Step — один логически завершённый модуль: один файл или один связанный набор функций.
- Тесты пишутся в рамках того же Step, что и реализация.
- Все тесты запускаются только через `./run_tests.sh` в Docker.

## Обзор этапов

```
Stage 001 — Foundation
    └► Stage 002 — API Core + Backup + Migration
            └► Stage 003a — Managers: минимум для запуска сети
                    └► Stage 003b — Managers: полное управление
```

| Stage | Что даёт |
|-------|---------|
| **001** Foundation | Domain-типы, порты, in-memory адаптер, mappers — чистое ядро без I/O |
| **002** API Core | Работающий HTTP API в кластере, данные мигрированы |
| **003a** Launch | NodeService, TokenService, Subscription — сеть физически запущена |
| **003b** Full | UserService write, DeviceService write, Rotation, Appeals — полное управление |

---

## Stage 001 — Foundation

**Цель:** Заложить ядро без I/O. Весь код этапа — чистый Go, тестируемый без запуска сервера или etcd.

### Scaffold

- [ ] `go.mod` + структура директорий (`cmd/`, `internal/`, `deploy/`)
- [ ] `Dockerfile.test` + `run_tests.sh`

### Domain

- [ ] `internal/domain/types.go` — defined types: `NodeIp`, `UserId`, `DeviceUuid`, `PubId`, `TokenId`, `AppealId`
- [ ] `internal/domain/enums.go` — `Status`, `NodeRole` и их константы
- [ ] `internal/domain/errors.go` — `NotFoundError`, `AlreadyExistsError`, `ValidationError`, `StorageError`
- [ ] `internal/domain/entities.go` — `User`, `Device`, `Node`, `Route`
- [ ] `internal/domain/entities_public.go` — `PublicUser`, `Message`, `Appeal`, `JoinToken`, `ApiToken`
- [ ] `internal/domain/validate.go` — функции валидации (`validateUsername`, и др.) + тесты

### Ports

- [ ] `internal/port/etcd.go` — `EtcdPort` interface + `TxnOp` struct
- [ ] `internal/port/clock.go` — `ClockPort` interface
- [ ] `internal/port/random.go` — `RandomPort` interface

### Adapters (тестовые)

- [ ] `internal/adapter/inmemory_etcd.go` — `InMemoryEtcd`: реализует `EtcdPort` через `map[string]string`, включая `CompareAndSwap` + тесты
- [ ] `internal/adapter/fake_clock.go` + `internal/adapter/fake_random.go` — детерминированные тестовые реализации

### Store: Records

- [ ] `internal/store/record/user.go` + `internal/store/record/device.go`
- [ ] `internal/store/record/node.go` + `internal/store/record/route.go`
- [ ] `internal/store/record/jointoken.go` + `internal/store/record/apitoken.go`
- [ ] `internal/store/record/appeal.go`

### Store: Mappers

- [ ] `internal/store/mapper/user.go` — `UserToKeys`, `RecordToUser`, round-trip тесты
- [ ] `internal/store/mapper/device.go` — аналогично + тесты
- [ ] `internal/store/mapper/node.go` + `internal/store/mapper/route.go` — аналогично + тесты
- [ ] `internal/store/mapper/jointoken.go` + `internal/store/mapper/apitoken.go` — аналогично + тесты
- [ ] `internal/store/mapper/appeal.go` — аналогично + тесты

### Store: Утилиты

- [ ] `internal/store/id_allocator.go` — `allocateID` через `CompareAndSwap` + тесты (success, retry, max retries exceeded)

---

## Stage 002 — API Core + Backup + Migration

**Цель:** Поднять работающий HTTP-сервер в k3s-mgmt. Мигрировать данные Arch 1.0 через `POST /api/v1/backup/load`.

### Adapter (production)

- [ ] `internal/adapter/etcd.go` — `EtcdAdapter`: реальный `go.etcd.io/etcd/client/v3` с mTLS + тесты адаптера (интеграционные, `./run_tests.sh integration`)

### Config

- [ ] `internal/config/config.go` — чтение env vars, валидация при старте, fail-fast если обязательная переменная отсутствует

### Services

- [ ] `internal/service/apitoken.go` — `ApiTokenService`: `Create`, `Validate`, `List`, `Revoke` + тесты
- [ ] `internal/service/backup.go` — `BackupService`: `Dump`, `Load` + тесты

### API: инфраструктура

- [ ] `internal/api/response.go` — хелперы `writeJSON`, `writeError`
- [ ] `internal/api/middleware/auth.go` — Bearer token middleware + тесты
- [ ] `internal/api/server.go` — chi-роутер, регистрация middleware и роутов

### API: handlers

- [ ] `internal/api/handler/health.go` — `GET /health`, `GET /api/v1/version` + тесты
- [ ] `internal/api/handler/apitokens.go` — `GET /api/v1/api-tokens`, `POST`, `DELETE /{id}` + тесты
- [ ] `internal/api/handler/backup.go` — `POST /api/v1/backup/dump`, `POST /api/v1/backup/load` + тесты

### Composition + Entry point

- [ ] `internal/api/composition.go` — DI: сборка адаптеров → сервисов → хендлеров
- [ ] `cmd/sigilgateapp/main.go` — точка входа: конфиг, composition, запуск сервера

### Deploy

- [ ] `deploy/` — K8s манифесты: `deployment.yaml`, `service.yaml`, `configmap-nginx.yaml`, `pvc.yaml`, `cronjob-certbot.yaml`, `secret.yaml.example`
- [ ] Деплой в k3s-mgmt + проверка `GET /health`
- [ ] Миграция данных: `POST /api/v1/backup/load` со snapshot Arch 1.0

---

## Stage 003a — Managers: минимум для запуска сети

**Цель:** Core-нода регистрируется через join-токен. Entry-поды видят маршруты. Пользователи получают subscription URL.

### NodeService

- [ ] `internal/service/node.go` — `Register`, `GetByIP`, `List`, `SetStatus` + тесты
- [ ] `internal/api/handler/nodes.go` — `GET /api/v1/nodes`, `POST`, `GET /{ip}`, `PATCH /{ip}/status` + тесты

### JoinToken Service

- [ ] `internal/service/token.go` — `Generate`, `Validate`, `Consume`, `Revoke` + тесты
- [ ] `internal/api/handler/tokens.go` — `POST /api/v1/tokens/join`, `GET /{token}`, `POST /{token}/consume`, `DELETE /{token}` + тесты

### CellService

- [ ] `internal/service/cell.go` — `List`, `GetByIP` (read-only view над Node) + тесты
- [ ] `internal/api/handler/cells.go` — `GET /api/v1/cells`, `GET /{ip}` + тесты

### RouteService (read + set)

- [ ] `internal/service/route.go` — `Set`, `GetByUUID`, `List` + тесты
- [ ] `internal/api/handler/routes.go` — `GET /api/v1/routes`, `GET /{uuid}`, `PUT /{uuid}` + тесты

### UserService (read-only)

- [ ] `internal/service/user.go` — `GetByID`, `List`, `GetDevices` + тесты
- [ ] `internal/api/handler/users.go` — `GET /api/v1/users`, `GET /{id}`, `GET /{id}/devices` + тесты

### DeviceService (read-only)

- [ ] `internal/service/device.go` — `GetByUUID` + тесты
- [ ] `internal/api/handler/devices.go` — `GET /api/v1/devices/{uuid}` + тесты

### Subscription

- [ ] `internal/api/handler/subscription.go` — `GET /subscription/{user_id}` (публичный, без auth) + тесты

---

## Stage 003b — Managers: полное управление

**Цель:** Telegram-бот и будущий CLI могут управлять пользователями, устройствами и ротацией.

### UserService (write)

- [ ] `internal/service/user.go` — добавить `Create`, `SetStatus` + тесты
- [ ] `internal/api/handler/users.go` — добавить `POST /api/v1/users`, `PATCH /{id}/status` + тесты

### DeviceService (write)

- [ ] `internal/service/device.go` — добавить `Add`, `SetStatus` + тесты
- [ ] `internal/api/handler/devices.go` — добавить `POST /api/v1/users/{id}/devices`, `PATCH /devices/{uuid}/status`, `DELETE /devices/{uuid}` + тесты

### RouteService (archive)

- [ ] `internal/service/route.go` — добавить `Archive` + тесты
- [ ] `internal/api/handler/routes.go` — добавить `DELETE /api/v1/routes/{uuid}` + тесты

### RotationService

- [ ] `internal/service/rotation.go` — `Rotate` (генерирует новый `serviceName` для ноды) + тесты
- [ ] `internal/api/handler/nodes.go` — добавить `POST /api/v1/nodes/{ip}/rotate` + тесты

### AppealService

- [ ] `internal/service/appeal.go` — `List`, `GetByID`, `SetStatus` + тесты
- [ ] `internal/api/handler/appeals.go` — `GET /api/v1/appeals`, `GET /{id}`, `PATCH /{id}/status` + тесты
