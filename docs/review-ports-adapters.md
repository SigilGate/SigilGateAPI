# Review: порты и адаптеры

## Краткий итог

Логика и алгоритмы в целом правильные — CompareAndSwap, PrefixScan, мьютексы поняты верно. Основные проблемы — в структуре пакетов (архитектурная ошибка) и несколько мест, которые не скомпилируются.

---

## Ошибки компиляции

### `adapter/inmemory_etcd.go` — `context` не импортирован

```go
// строка 17
func (e *InMemoryETCD) Get(_ context.Context, key string) (*string, error) {
```

`context` нигде не импортирован, но используется в сигнатурах всех методов. Это сразу `undefined: context`.

---

### `adapter/inmemory_etcd.go` — `TxnOp` не импортирован

```go
// строка 57
func (e *InMemoryETCD) Txn(_ context.Context, ops []TxnOp) error {
```

`TxnOp` определён в пакете `etcd` (`port/etcd.go`). В `inmemory_etcd` он не импортируется. Компилятор не найдёт тип.

---

### `adapter/inmemory_etcd.go` — два бага в `Txn`, строка 64

```go
// написано:
s.store[op.Key] = op.Value

// должно быть:
e.store[op.Key] = *op.Value
```

Две ошибки в одной строке:
- `s` — неизвестная переменная. Ресивер называется `e`.
- `op.Value` имеет тип `*string`, а не `string`. Нужно разыменовать: `*op.Value`.

---

### `adapter/fake_random.go` — синтаксическая ошибка в конструкторе

```go
// написано:
return &FakeRandom

// должно быть:
return &FakeRandom{}
```

`&FakeRandom` — это адрес типа, а не значения. Без `{}` код не скомпилируется.

---

## Архитектурная ошибка: пакеты

Это самая важная проблема — все остальные файлы написаны хорошо.

### Что сделано

Каждый файл объявлен в отдельном пакете:

```
port/etcd.go    → package etcd
port/clock.go   → package clock
port/random.go  → package random

adapter/inmemory_etcd.go → package inmemory_etcd
adapter/fake_clock.go    → package fake_clock
adapter/fake_random.go   → package fake_random
```

### Почему это неправильно

В Go пакет — это **единица инкапсуляции**, не файл. Имя пакета определяется директорией, а не именем файла. Все файлы в одной директории **обязаны** иметь одинаковое имя пакета (кроме `_test`).

Текущая структура означает: в директории `internal/port/` три файла с разными пакетами (`etcd`, `clock`, `random`). Это не скомпилируется — Go выдаст ошибку `found packages etcd and clock in .../internal/port`.

### Как правильно

Все файлы в директории `internal/port/` — пакет `port`. Все файлы в `internal/adapter/` — пакет `adapter`.

```go
// port/etcd.go
package port

// port/clock.go
package port

// port/random.go
package port
```

```go
// adapter/inmemory_etcd.go
package adapter

// adapter/fake_clock.go
package adapter

// adapter/fake_random.go
package adapter
```

Тогда импорты в сервисах будут выглядеть так:

```go
import (
    "github.com/sigilgate/sigilgateapi/internal/port"
    "github.com/sigilgate/sigilgateapi/internal/adapter"
)

var etcd port.EtcdPort = adapter.NewInMemoryEtcd()
```

---

## Логическая ошибка: `PrefixScan` в интерфейсе не возвращает `error`

```go
// port/etcd.go — написано:
PrefixScan(ctx context.Context, prefix string) (map[string]string)

// реализация в inmemory_etcd.go:
func (e *InMemoryETCD) PrefixScan(...) (map[string]string, error) {
```

Интерфейс и реализация расходятся. По спецификации — и это правильно — все методы I/O должны возвращать `error`. Реальный etcd-адаптер может вернуть ошибку сети. Исправь интерфейс:

```go
PrefixScan(ctx context.Context, prefix string) (map[string]string, error)
```

---

## Мелкие замечания

### Пробелы перед списком параметров

```go
// написано:
Get (ctx context.Context, key string) (*string, error)

// идиоматично:
Get(ctx context.Context, key string) (*string, error)
```

`gofmt` (стандартный форматтер Go) убирает эти пробелы. Код компилируется, но это нарушение стиля — в Go пробел между именем функции/метода и `(` не принят.

---

### Лишняя проверка в `Delete`

```go
// написано:
if _, ok := e.store[key]; ok {
    delete(e.store, key)
}

// достаточно:
delete(e.store, key)
```

`delete` в Go — no-op при отсутствии ключа. Дополнительная проверка ничего не добавляет, только загромождает.

---

### Compile-time проверка реализации интерфейса

В спецификации (001-08) упоминается полезный паттерн:

```go
var _ port.EtcdPort = (*InMemoryETCD)(nil)
```

Эта строка не делает ничего в runtime, но если `InMemoryETCD` перестанет реализовывать `EtcdPort` — компилятор сразу укажет на это. Полезно добавить в каждый адаптер.

---

## Итог по файлам

| Файл | Статус | Критичные проблемы |
|------|--------|--------------------|
| `port/etcd.go` | не скомпилируется | неверный пакет, `PrefixScan` без `error` |
| `port/clock.go` | не скомпилируется | неверный пакет |
| `port/random.go` | не скомпилируется | неверный пакет |
| `adapter/inmemory_etcd.go` | не скомпилируется | неверный пакет, `context` не импортирован, `TxnOp` не импортирован, `s.store` + `op.Value` без разыменования |
| `adapter/fake_clock.go` | не скомпилируется | неверный пакет |
| `adapter/fake_random.go` | не скомпилируется | неверный пакет, `&FakeRandom` без `{}` |
