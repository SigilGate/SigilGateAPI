# 001-18 · Store Mapper: node.go + route.go

**Файлы:** `internal/store/mapper/node.go`, `internal/store/mapper/route.go`

---

## Node — несколько опциональных полей

`Domain`, `ClientServiceName`, `CoreServiceName`, `CellDomain`, `UUID` — все `*string`/`*CellDomain` в domain, `string` в record. Mapper применяет один и тот же паттерн для каждого:

```go
// domain → etcd: пишем только если не nil
if n.Domain != nil {
    ops = append(ops, port.TxnOp{Key: base + "domain", Value: n.Domain})
}

// etcd → domain: "" → nil
var domain *string
if r.Domain != "" {
    domain = &r.Domain
}
```

`NodeNumber` — `*int` в domain, строка в record:

```go
// domain → etcd
if n.NodeNumber != nil {
    ops = append(ops, port.TxnOp{Key: base + "node_number", Value: ptr(strconv.Itoa(*n.NodeNumber))})
}

// etcd → domain
var nodeNumber *int
if r.NodeNumber != "" {
    n, err := strconv.Atoi(r.NodeNumber)
    if err != nil {
        return domain.Node{}, fmt.Errorf("parse node_number: %w", err)
    }
    nodeNumber = &n
}
```

Роль ноды определяет какие из этих полей будут заполнены: у `core` — `CoreServiceName`, `CellDomain`, `NodeNumber`, `UUID`; у `entry` — `ClientServiceName`; у `mgmt` — ни одного.

---

## Route — простейший mapper

`Route` состоит только из скалярных полей без опциональных. Mapper минимален — хороший первый mapper для практики.
