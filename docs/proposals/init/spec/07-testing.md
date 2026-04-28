# 07. Тестирование

## Принцип

Каждый слой тестируется на своём уровне с минимальными зависимостями. Чем ближе тест к `domain/`, тем чище: никаких моков, никакого I/O, только данные.

## Уровни тестирования

### 1. Domain-тесты (`internal/domain/`)

Чистые unit-тесты без моков и без I/O.

Что тестируется:
- Валидация доменных правил (пустой username, недопустимый статус и т.д.)
- Корректность типизированных ошибок
- Чистые трансформации (если есть domain-логика)

```go
func TestValidateUsernameEmpty(t *testing.T) {
    err := validateUsername("")
    require.Error(t, err)
    var ve *ValidationError
    assert.ErrorAs(t, err, &ve)
    assert.Equal(t, "username", ve.Field)
}

func TestValidateUsernameToolong(t *testing.T) {
    err := validateUsername(strings.Repeat("a", 33))
    assert.ErrorAs(t, err, &ValidationError{})
}
```

### 2. Mapper-тесты (`internal/store/mapper/`)

Round-trip тесты без I/O. Тестируют корректность сериализации/десериализации.

```go
func TestUserRoundTrip(t *testing.T) {
    original := domain.User{
        ID:       1,
        Username: "<username>",
        Status:   domain.StatusActive,
        // ...
    }
    record := UserToRecord(original)
    restored, err := RecordToUser(record)
    require.NoError(t, err)
    assert.Equal(t, original, restored)
}

func TestUserRecordKeys(t *testing.T) {
    user := domain.User{ID: 1, Username: "<username>"}
    keys := UserToKeys(user)
    assert.Contains(t, keys, TxnOp{Key: "/sigilgate/users/1/username", Value: "<username>"})
}
```

### 3. Service-тесты (`internal/service/`)

Тестируют use-case'ы с in-memory реализацией `EtcdPort`. Никакого реального I/O.

```go
func TestCreateUserSuccess(t *testing.T) {
    etcd  := adapter.NewInMemoryEtcd()
    clock := adapter.NewFakeClock(time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC))
    svc   := service.NewUserService(etcd, clock, adapter.NewFakeRandom())

    user, err := svc.Create(context.Background(), "<username>", nil)
    require.NoError(t, err)
    assert.Equal(t, "<username>", user.Username)
    assert.Equal(t, domain.StatusActive, user.Status)
}

func TestCreateUserDuplicateUsername(t *testing.T) {
    etcd := adapter.NewInMemoryEtcd()
    svc  := service.NewUserService(etcd, fakeClock(), fakeRandom())

    _, err := svc.Create(context.Background(), "<username>", nil)
    require.NoError(t, err)

    _, err = svc.Create(context.Background(), "<username>", nil)
    require.Error(t, err)
    assert.ErrorAs(t, err, &domain.AlreadyExistsError{})
}
```

### 4. API-тесты (`internal/api/handler/`)

Тестируют HTTP-слой с `httptest` и in-memory etcd. Проверяют: маршрутизацию, аутентификацию, HTTP-коды, форматы ответов.

```go
func TestGetUserNotFound(t *testing.T) {
    app := newTestApp(t)
    req := httptest.NewRequest("GET", "/api/v1/users/999", nil)
    req.Header.Set("Authorization", "Bearer test-token")
    rec := httptest.NewRecorder()

    app.ServeHTTP(rec, req)

    assert.Equal(t, 404, rec.Code)
    var body map[string]any
    require.NoError(t, json.Unmarshal(rec.Body.Bytes(), &body))
    assert.Equal(t, "not_found", body["error"])
}

func TestUnauthenticatedRequest(t *testing.T) {
    app := newTestApp(t)
    req := httptest.NewRequest("GET", "/api/v1/users", nil)
    rec := httptest.NewRecorder()
    app.ServeHTTP(rec, req)
    assert.Equal(t, 401, rec.Code)
}

func TestCreateAndGetUser(t *testing.T) {
    app  := newTestApp(t)
    auth := map[string]string{"Authorization": "Bearer test-token"}

    body := `{"username": "<username>"}`
    create := doRequest(t, app, "POST", "/api/v1/users", body, auth)
    assert.Equal(t, 201, create.Code)

    var created map[string]any
    require.NoError(t, json.Unmarshal(create.Body.Bytes(), &created))
    id := int(created["id"].(float64))

    get := doRequest(t, app, "GET", fmt.Sprintf("/api/v1/users/%d", id), "", auth)
    assert.Equal(t, 200, get.Code)
}
```

### 5. Adapter-тесты (`internal/adapter/`)

Интеграционные тесты с реальным etcd. Запускаются только в Docker-окружении (через `docker compose`).

Что тестируется:
- Реальные Put/Get/Delete/PrefixScan через mTLS
- Транзакции (Txn): атомарность создания объектов
- CompareAndSwap: корректность при конкурентных записях
- Поведение при недоступном etcd → `*StorageError`

Эти тесты запускаются отдельно: `./run_tests.sh integration`.

## Организация тестов

```
internal/
├── domain/
│   ├── entities_test.go
│   └── ...
├── store/
│   └── mapper/
│       ├── user_test.go
│       └── ...
├── service/
│   ├── user_test.go
│   └── ...
├── api/
│   └── handler/
│       ├── users_test.go
│       ├── auth_test.go
│       └── ...
└── adapter/
    └── etcd_test.go        ← только интеграционные, требуют Docker
```

Вспомогательные хелперы (`newTestApp`, `doRequest`, `fakeClock`, `fakeRandom`) — в `internal/testutil/` или в `_test.go` файлах соответствующего пакета.

## Запуск

```bash
# Unit + API тесты (в контейнере, без внешних зависимостей)
./run_tests.sh

# Интеграционные тесты (требует Docker + etcd sidecar)
./run_tests.sh integration

# Все тесты
./run_tests.sh all
```

Локальный запуск (`go test ./...`) **НЕ ДОПУСТИМ**.
Единственный допустимый вариант запуска тестов — контейнерный запуск через `./run_tests.sh`.

## Правила

- **Тест = документация.** Имя теста описывает поведение: `TestCreateUserDuplicateUsernameReturnsAlreadyExists`, не `TestCreateUser2`.
- **Один assert на концепцию.** Несколько `assert` в тесте допустимы, если они проверяют одно поведение.
- **Никаких реальных дат/UUID в фикстурах.** Только через `FakeClock` и `FakeRandom` — тесты детерминированы.
- **Нет спящих тестов.** `time.Sleep` в тестах запрещён.
- **Интеграционные тесты изолированы** — не смешиваются с unit-тестами в одном `./run_tests.sh`.
- **`require` vs `assert`**: `require` останавливает тест при провале (используй для предусловий), `assert` продолжает (используй для проверок результата).
