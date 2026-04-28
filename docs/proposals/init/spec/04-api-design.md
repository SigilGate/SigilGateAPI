# 04. Дизайн API

## Общие принципы

- **REST** — ресурсо-ориентированный дизайн. URL — существительные, HTTP-методы — глаголы.
- **JSON** — единственный формат запросов и ответов. `Content-Type: application/json`.
- **Stateless** — каждый запрос самодостаточен. Сессий нет.
- **Versioning** — URL-prefix `/api/v1/`. Смена мажорной версии не ломает старых клиентов.
- **Идемпотентность** — GET, PUT, DELETE идемпотентны. POST — нет.

## Базовый URL

```
https://<DOMAIN>/api/v1/
```

Примеры:

```
https://<DOMAIN>/api/v1/users
https://<DOMAIN>/api/v1/devices
```

Внутри кластера (для BackupSvc, ботов):
```
https://sigilgateapp.<NAMESPACE>.svc.cluster.local/api/v1/
```

## Аутентификация

```
Authorization: Bearer <token>
```

Отсутствие заголовка или невалидный токен → `401 Unauthorized`.
Валидный токен без нужных прав → `403 Forbidden`.

Эндпоинт `/health` не требует аутентификации.

## Формат ошибок

```json
{
  "error": "not_found",
  "message": "Пользователь с id=42 не найден",
  "detail": {}
}
```

| HTTP статус | Код ошибки | Ситуация |
|-------------|-----------|---------|
| 400 | `bad_request` | Невалидный JSON в теле запроса |
| 401 | `unauthorized` | Отсутствует или невалиден Bearer token |
| 403 | `forbidden` | Токен валиден, но нет прав |
| 404 | `not_found` | Сущность не найдена |
| 409 | `already_exists` | Конфликт уникальности |
| 422 | `validation_error` | Нарушение бизнес-правил |
| 503 | `storage_unavailable` | Ошибка соединения с etcd |

## Эндпоинты

### Служебные

```
GET  /health              → 200 {"status": "ok", "etcd": "ok" | "degraded"}
GET  /api/v1/version      → 200 {"version": "0.1.0"}
```

---

### Пользователи — `/api/v1/users`

```
GET    /api/v1/users                    ← список; query: ?status=active
POST   /api/v1/users                    ← создать пользователя
GET    /api/v1/users/{id}               ← получить пользователя
PATCH  /api/v1/users/{id}/status        ← изменить статус
GET    /api/v1/users/{id}/devices       ← устройства пользователя
```

**POST /api/v1/users**
```json
// request
{"username": "<username>", "hash_telegram_id": "<hmac_sha256>"}

// response 201
{"id": 42, "username": "<username>", "status": "active", "created": "2026-04-19"}
```

**PATCH /api/v1/users/{id}/status**
```json
// request
{"status": "inactive"}

// response 200
{"id": 42, "status": "inactive", "status_at": "2026-04-19"}
```

---

### Устройства — `/api/v1/devices`

```
POST   /api/v1/users/{id}/devices       ← добавить устройство пользователю
GET    /api/v1/devices/{uuid}           ← получить устройство (по UUID, без user_id)
PATCH  /api/v1/devices/{uuid}/status    ← изменить статус
DELETE /api/v1/devices/{uuid}           ← архивировать (soft delete)
```

**POST /api/v1/users/{id}/devices**
```json
// request
{"name": "<device_name>"}

// response 201
{"uuid": "<uuid>", "user_id": 42, "name": "<device_name>", "status": "active", "created": "2026-04-19"}
```

---

### Ноды — `/api/v1/nodes`

```
GET    /api/v1/nodes                    ← список; query: ?role=core&status=active
POST   /api/v1/nodes                    ← зарегистрировать ноду
GET    /api/v1/nodes/{ip}               ← получить ноду
PATCH  /api/v1/nodes/{ip}/status        ← изменить статус
POST   /api/v1/nodes/{ip}/rotate        ← сгенерировать новый serviceName
```

**POST /api/v1/nodes**
```json
// request
{"ip": "<NODE_IP>", "role": "core", "domain": "<NODE_DOMAIN>", "core_service_name": "<service_name>"}

// response 201
{"ip": "<NODE_IP>", "role": "core", "domain": "<NODE_DOMAIN>", "status": "active"}
```

**POST /api/v1/nodes/{ip}/rotate**
```json
// response 200
{"ip": "<NODE_IP>", "service_name": "<new_service_name>", "rotated_at": "2026-04-19T12:00:00Z"}
```

**POST /api/v1/nodes/join** *(без Bearer-авторизации)*
```json
// request
{
  "join_token": "<uuid>",
  "ip": "<NODE_IP>",
  "uuid": "<xray-uuid>",
  "core_service_name": "<serviceName>"
}

// response 201
{
  "ip": "<NODE_IP>",
  "role": "core",
  "domain": "3.core.necodate.website",
  "cell_domain": "necodate.website",
  "node_number": 3,
  "status": "active"
}
```

> Вызывается Core-контейнером при старте. Аутентификация — join-токен в теле запроса. `domain`, `cell_domain`, `node_number` берутся из токена — оператор не передаёт их при запуске контейнера. Токен потребляется атомарно внутри этого эндпоинта.

---

### Маршруты — `/api/v1/routes`

```
GET    /api/v1/routes                   ← список; query: ?status=active
GET    /api/v1/routes/{uuid}            ← получить маршрут (uuid = device uuid)
PUT    /api/v1/routes/{uuid}            ← назначить/обновить маршрут
DELETE /api/v1/routes/{uuid}            ← архивировать
```

**PUT /api/v1/routes/{uuid}**
```json
// request
{"core_ip": "<NODE_IP>"}

// response 200
{"uuid": "<uuid>", "core_ip": "<NODE_IP>", "status": "active", "status_at": "2026-04-19"}
```

---

### Ячейки — `/api/v1/cells`

Ячейка привязана к домену первого уровня. Core-ноды получают поддомен `{N}.core.{domain}`, где N — атомарный счётчик, инкрементируемый при выпуске join-токена.

```
GET    /api/v1/cells                    ← список; query: ?status=active
POST   /api/v1/cells                    ← создать ячейку
GET    /api/v1/cells/{domain}           ← получить ячейку
PATCH  /api/v1/cells/{domain}/status    ← пометить скомпрометированной, деактивировать
GET    /api/v1/cells/{domain}/nodes     ← ноды ячейки
```

---

### Join-токены — `/api/v1/tokens/join`

```
POST   /api/v1/tokens/join                        ← выпустить токен (24ч, одноразовый)
GET    /api/v1/tokens/join/{token}                ← проверить токен (использован ли, истёк ли)
POST   /api/v1/tokens/join/{token}/consume        ← пометить использованным (одноразово)
DELETE /api/v1/tokens/join/{token}                ← отозвать токен
```

**POST /api/v1/tokens/join**
```json
// request
{"cell_domain": "necodate.website"}

// response 201
{
  "token": "<uuid>",
  "expires_at": "2026-04-20T12:00:00Z",
  "node_number": 3,
  "assigned_domain": "3.core.necodate.website"
}
```

> `node_number` и `assigned_domain` присваиваются атомарно (CAS-счётчик `/sigilgate/cells/{domain}/core_node_counter`). Оператор использует `assigned_domain` для создания DNS A-записи и получения TLS-сертификата через certbot до запуска контейнера.

**POST /api/v1/tokens/join/{token}/consume**
```json
// response 200 — токен успешно помечен использованным
{"token": "<uuid>", "used": true}

// 409 если токен уже использован
// 404 если токен не найден или истёк
```

> В MVP: потребление токена происходит автоматически внутри `POST /api/v1/nodes/join`. В целевой архитектуре (с CSR/mTLS): Core Registration Service вызывает этот эндпоинт после выпуска сертификата.

---

### Обращения — `/api/v1/appeals`

```
GET    /api/v1/appeals                  ← список; query: ?status=active
GET    /api/v1/appeals/{id}             ← получить обращение
PATCH  /api/v1/appeals/{id}/status      ← принять, закрыть, архивировать
```

> `POST /api/v1/appeals` (создание обращения) — вне текущего scope. Существующие обращения загружаются через `POST /api/v1/backup/load`. Эндпоинт создания будет определён позже.

---

### PublicUser

Управление `PublicUser` — вне текущего scope. Начальные данные загружаются через `POST /api/v1/backup/load`. Эндпоинты будут определены в отдельном этапе.

---

### Backup — `/api/v1/backup`

```
POST   /api/v1/backup/dump              ← etcd → snapshot JSON
POST   /api/v1/backup/load              ← snapshot JSON → etcd
```

**POST /api/v1/backup/dump — response**
```json
{
  "keys_count": 342,
  "namespaces": ["/sigilgate/", "/public/"],
  "snapshot": { "/sigilgate/users/1/username": "<username>", ... }
}
```

---

### API-токены — `/api/v1/api-tokens`

```
GET    /api/v1/api-tokens               ← список токенов (без plaintext значений)
POST   /api/v1/api-tokens               ← создать токен; response: plaintext один раз
DELETE /api/v1/api-tokens/{id}          ← отозвать токен
```

**POST /api/v1/api-tokens**
```json
// request
{"name": "telegram-bot"}

// response 201 — plaintext только один раз
{"token_id": "<uuid>", "name": "telegram-bot", "token": "sgat_<random>"}
```

## Коллекции

Эндпоинты списков возвращают массив объектов напрямую или обёртку `{"items": [...]}`. Пагинация не определена — все объекты возвращаются за один запрос. При необходимости пагинация будет добавлена позже.
