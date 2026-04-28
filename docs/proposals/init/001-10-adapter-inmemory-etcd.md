# 001-10 · Adapter: inmemory_etcd.go

**Файл:** `internal/adapter/inmemory_etcd.go`

---

## Python → Go

```python
class InMemoryEtcd:
    def __init__(self):
        self._store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)
```

```go
type InMemoryEtcd struct {
    mu    sync.Mutex
    store map[string]string
}

func NewInMemoryEtcd() *InMemoryEtcd {
    return &InMemoryEtcd{store: make(map[string]string)}
}

func (e *InMemoryEtcd) Get(_ context.Context, key string) (*string, error) {
    e.mu.Lock()
    defer e.mu.Unlock()
    v, ok := e.store[key]
    if !ok {
        return nil, nil
    }
    return &v, nil
}
```

---

## sync.Mutex — зачем в тестах

Go-тесты могут запускаться параллельно (`t.Parallel()`). Map в Go не потокобезопасна — конкурентная запись вызывает панику. Mutex делает реализацию корректной независимо от контекста использования.

---

## CompareAndSwap

```go
func (e *InMemoryEtcd) CompareAndSwap(_ context.Context, key string, expected *string, value string) (bool, error) {
    e.mu.Lock()
    defer e.mu.Unlock()
    current, exists := e.store[key]
    if expected == nil {
        if exists {
            return false, nil // ожидали отсутствия ключа, а он есть
        }
    } else {
        if !exists || current != *expected {
            return false, nil
        }
    }
    e.store[key] = value
    return true, nil
}
```

`expected == nil` означает «ключ не должен существовать» — для первого запуска счётчика ID.
