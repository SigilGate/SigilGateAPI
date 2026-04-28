# 001-13 · Store Record: node.go + route.go

**Файлы:** `internal/store/record/node.go`, `internal/store/record/route.go`

---

## Тот же паттерн

```go
type NodeRecord struct {
    IP                string
    Role              string
    Domain            string // "" = не задан
    ClientServiceName string
    CoreServiceName   string
    CellDomain        string // "" = не задан (только у core-нод)
    NodeNumber        string // "" = не задан; int хранится как строка
    UUID              string // "" = не задан (только у core-нод)
    Status            string
    StatusAt          string
}

type RouteRecord struct {
    UUID     string
    CoreIP   string
    Status   string
    StatusAt string
}
```

---

## Опциональные поля Node

В domain: `Domain *string`, `ClientServiceName *string`, `CoreServiceName *string`, `CellDomain *CellDomain`, `NodeNumber *int`, `UUID *string`.  
В record: обычные `string`. Mapper преобразует `""` → `nil` и обратно.

`NodeNumber` — хранится в etcd как строка (`strconv.Itoa` / `strconv.Atoi`), в domain — `*int`.

Это соглашение для всех record'ов: `""` в record = `nil` в domain.
