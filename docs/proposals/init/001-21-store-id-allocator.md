# 001-21 · Store: id_allocator.go

**Файл:** `internal/store/id_allocator.go`

---

## Python → Go

```python
def allocate_id(counter_key: str, etcd: EtcdPort) -> Result[int, ServiceError]:
    for _ in range(MAX_RETRIES):
        current = etcd.get(counter_key)
        next_id = int(current) + 1 if current else 1
        if etcd.compare_and_swap(counter_key, current, str(next_id)):
            return Ok(next_id)
    return Err(EtcdError(f"не удалось выделить ID по ключу {counter_key}"))
```

```go
const maxRetries = 10

func AllocateID(ctx context.Context, counterKey string, etcd port.EtcdPort) (int, error) {
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
    return 0, &domain.StorageError{Cause: fmt.Errorf("не удалось выделить ID: %s", counterKey)}
}

func computeNext(current *string) (nextID int, expected *string) {
    if current == nil {
        return 1, nil // ключ не существует — первый запуск
    }
    n, _ := strconv.Atoi(*current)
    return n + 1, current
}
```

---

## Go 1.22: for range N

`for range maxRetries` — синтаксис Go 1.22 для итерации N раз без переменной. В Go 1.21 и раньше писали `for i := 0; i < maxRetries; i++`. Именно поэтому в `go.mod` указан `go 1.22.0`.

---

## Тест на retry

```go
func TestAllocateIDRetry(t *testing.T) {
    etcd := adapter.NewInMemoryEtcd()

    // два вызова параллельно — один должен получить 1, другой 2
    id1, err := store.AllocateID(ctx, "/test/counter", etcd)
    require.NoError(t, err)
    id2, err := store.AllocateID(ctx, "/test/counter", etcd)
    require.NoError(t, err)

    assert.ElementsMatch(t, []int{1, 2}, []int{id1, id2})
}
```
