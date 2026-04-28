# 001-02 · Domain: types.go

**Файл:** `internal/domain/types.go`

---

## Python → Go

В Python использовался `NewType` из `typing`:

```python
from typing import NewType

NodeIp = NewType("NodeIp", str)
UserId = NewType("UserId", int)
```

`NewType` — это инструмент статического анализатора (mypy). В runtime `NodeIp("1.2.3.4")` — это просто `str`. Защита существует только на уровне аннотаций.

В Go — **defined type**: полноценный отдельный тип на уровне компилятора.

```go
type NodeIp string
type UserId int
```

---

## Ключевое отличие: компилятор не позволит перепутать

```go
func getNode(ip NodeIp) { ... }

var raw string = "1.2.3.4"
getNode(raw) // compile error: cannot use raw (type string) as type NodeIp
```

В Python аналогичная ошибка была бы поймана только mypy — не интерпретатором.

---

## Явное приведение обязательно

Когда нужна голая строка — явно преобразуем:

```go
ip := NodeIp("1.2.3.4")

// передать в etcd — нужна string:
etcd.Get(ctx, "/sigilgate/nodes/" + string(ip))

// обратно из etcd:
ip = NodeIp(rawStringFromEtcd)
```

Это немного многословнее, чем в Python, зато граница между «строкой как строкой» и «строкой как IP-адресом ноды» видна явно в коде.

---

## UserId — то же самое для int

```go
type UserId int

id := UserId(42)

// в etcd хранится как строка — явное преобразование:
etcd.Put(ctx, key, strconv.Itoa(int(id)))

// из etcd:
n, _ := strconv.Atoi(rawValue)
id = UserId(n)
```

Двойное приведение `int(id)` → `strconv.Itoa(...)` выглядит многословно, но это весь «налог» за безопасность типов. Всё это локализовано в mapper'е — в остальном коде работаем только с `UserId`.

---

## Где живут эти типы

Все defined types — в одном файле `internal/domain/types.go`. Они не содержат методов и логики — только определения. Используются по всему `internal/`: в entities, service, mapper, handler.
