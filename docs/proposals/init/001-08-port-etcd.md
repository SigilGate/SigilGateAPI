# 001-08 · Port: etcd.go

**Файл:** `internal/port/etcd.go`

---

## Python → Go

```python
class EtcdPort(Protocol):
    def get(self, key: str) -> str | None: ...
    def put(self, key: str, value: str) -> None: ...
    def compare_and_swap(self, key: str, expected: str | None, value: str) -> bool: ...
```

```go
type EtcdPort interface {
    Get(ctx context.Context, key string) (*string, error)
    Put(ctx context.Context, key, value string) error
    Delete(ctx context.Context, key string) error
    PrefixScan(ctx context.Context, prefix string) (map[string]string, error)
    Txn(ctx context.Context, ops []TxnOp) error
    CompareAndSwap(ctx context.Context, key string, expected *string, value string) (bool, error)
}

type TxnOp struct {
    Key   string
    Value *string // nil = DELETE
}
```

---

## Два Go-специфичных момента

**`context.Context` первым параметром.** Это конвенция Go для любой операции с I/O. Context несёт дедлайн и сигнал отмены — etcd-клиент отменит запрос, если контекст закрыт. В Python этого не было.

**Неявное удовлетворение интерфейса.** В Python `EtcdAdapter` явно наследовал `Protocol`. В Go — никакого `implements`. Если структура имеет все нужные методы с правильными сигнатурами, она автоматически удовлетворяет интерфейсу. Компилятор проверяет это в точке использования.

```go
// проверка что EtcdAdapter реализует EtcdPort — на этапе компиляции:
var _ port.EtcdPort = (*adapter.EtcdAdapter)(nil)
```

Эту строку можно добавить в `adapter/etcd.go` — она ничего не делает в runtime, но компилятор сразу скажет если интерфейс не реализован.
