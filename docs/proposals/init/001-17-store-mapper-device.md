# 001-17 · Store Mapper: device.go

**Файл:** `internal/store/mapper/device.go`

---

## Тот же паттерн, одна особенность

`Device.CoreNode *NodeIp` — опциональный указатель на defined type. В etcd: пустая строка = не назначен.

```go
// domain → etcd
if d.CoreNode != nil {
    ops = append(ops, port.TxnOp{Key: base + "core_node", Value: ptr(string(*d.CoreNode))})
}

// etcd → domain
var coreNode *domain.NodeIp
if r.CoreNode != "" {
    n := domain.NodeIp(r.CoreNode)
    coreNode = &n
}
```

Двойное разыменование `*d.CoreNode` — сначала разыменовываем указатель (`*NodeIp` → `NodeIp`), потом приводим defined type к string (`NodeIp` → `string`). В Python это был просто `device.core_node`.
