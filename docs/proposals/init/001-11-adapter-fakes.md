# 001-11 · Adapter: fake_clock.go + fake_random.go

**Файлы:** `internal/adapter/fake_clock.go`, `internal/adapter/fake_random.go`

---

## FakeClock

```go
type FakeClock struct {
    fixed time.Time
}

func NewFakeClock(t time.Time) *FakeClock {
    return &FakeClock{fixed: t}
}

func (c *FakeClock) Now() time.Time {
    return c.fixed
}
```

Возвращает одно и то же время при каждом вызове. Тесты становятся детерминированными: `user.Created` всегда равен тому, что передано в `NewFakeClock`.

---

## FakeRandom

```go
type FakeRandom struct {
    counter int
}

func NewFakeRandom() *FakeRandom {
    return &FakeRandom{}
}

func (r *FakeRandom) UUID() string {
    r.counter++
    return fmt.Sprintf("00000000-0000-0000-0000-%012d", r.counter)
}
```

Последовательные UUID вместо случайных. В тестах первое устройство всегда получает `...000000000001`, второе — `...000000000002`. Удобно для `assert.Equal`.
