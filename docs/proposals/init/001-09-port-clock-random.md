# 001-09 · Port: clock.go + random.go

**Файлы:** `internal/port/clock.go`, `internal/port/random.go`

---

## Тот же паттерн, что EtcdPort

```go
// clock.go
type ClockPort interface {
    Now() time.Time
}

// random.go
type RandomPort interface {
    UUID() string
}
```

Смысл — тот же, что в Python: запрет на прямые вызовы `time.Now()` и `uuid.uuid4()` внутри сервисного слоя. Через порт — тестируемо и детерминировано.

---

## Зачем это в Go

В Python `datetime.now()` и `uuid.uuid4()` легко мокировать через `unittest.mock.patch`. В Go моков нет — зависимости передаются явно. Порт + фейковая реализация = полный контроль в тестах без магии.

```go
// в тесте:
clock := adapter.NewFakeClock(time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC))
svc   := service.NewUserService(etcd, clock, fakeRandom)

user, _ := svc.Create(ctx, "alice", nil)
assert.Equal(t, clock.Now(), user.Created) // детерминировано
```
