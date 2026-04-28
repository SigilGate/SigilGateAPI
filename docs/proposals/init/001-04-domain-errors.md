# 001-04 · Domain: errors.go

**Файл:** `internal/domain/errors.go`

---

## Python → Go

```python
@dataclass(frozen=True)
class NotFound:
    entity: str
    key: str
```

В Python ошибки были значениями в `Result[T, E]` — не исключениями. В Go ошибки тоже значения, но через встроенный интерфейс `error`:

```go
type NotFoundError struct {
    Resource string
    ID       string
}

func (e *NotFoundError) Error() string {
    return fmt.Sprintf("%s %q not found", e.Resource, e.ID)
}
```

Метод `Error() string` — это весь интерфейс `error`. Любая структура с этим методом автоматически является `error`.

---

## errors.As вместо isinstance / match/case

В Python разбор ошибки выглядел так:

```python
match result:
    case Err(NotFound(entity, key)): ...
    case Err(EtcdError()): ...
```

В Go — через `errors.As`:

```go
var notFound *NotFoundError
switch {
case errors.As(err, &notFound):
    writeError(w, 404, "not_found", notFound.Error())
case err != nil:
    writeError(w, 503, "storage_unavailable", "")
}
```

`errors.As` проверяет цепочку оборачивания (`%w`) — находит нужный тип даже если ошибка обёрнута несколько раз.

---

## Все типы ошибок в одном файле

`NotFoundError`, `AlreadyExistsError`, `ValidationError`, `StorageError` — все четыре здесь. Каждый — отдельная структура с методом `Error()`.
