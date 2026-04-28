# 06. Стиль кода

## Принципы

Эти правила применяются ко всему коду в репозитории. Исключения фиксируются явно с обоснованием.

## Типизация

- **Статическая типизация** — Go типизирован статически по умолчанию. Не используется `interface{}` / `any` там, где известен конкретный тип.
- **Defined types для идентификаторов** — `type NodeIp string`, `type UserId int`. Голые `string` / `int` только для примитивных значений без семантики ссылки.
- **Указатели для необязательных полей** — `*string`, `*time.Time` вместо sentinel-значений (`""`, нулевого времени).

## Иммутабельность

Go не имеет встроенного механизма заморозки структур. Иммутабельность обеспечивается соглашением:

- Функции сервисного слоя принимают domain-объект и возвращают новый — не модифицируют переданный.
- Поля структур экспортированы (для `encoding/json`, тестирования), но никогда не изменяются снаружи конструктора.
- Конструкторы возвращают значение, не указатель, где это возможно.

```go
// правильно: возвращаем изменённую копию
func withStatus(u domain.User, s domain.Status, at time.Time) domain.User {
    u.Status   = s
    u.StatusAt = at
    return u
}

// неправильно: мутация переданного значения через указатель без явной необходимости
func setStatus(u *domain.User, s domain.Status) {
    u.Status = s
}
```

## Обработка ошибок

Ошибки — значения. Сигнатура: `(T, error)`. Никаких `panic` в бизнес-логике.

### Типизированные ошибки в domain/

```go
type NotFoundError struct {
    Resource string
    ID       string
}
func (e *NotFoundError) Error() string {
    return fmt.Sprintf("%s %q not found", e.Resource, e.ID)
}
```

### Возврат ошибок в сервисном слое

```go
func (s *UserService) GetByID(ctx context.Context, id domain.UserId) (domain.User, error) {
    rec, err := s.etcd.Get(ctx, userKey(id))
    if err != nil {
        return domain.User{}, &domain.StorageError{Cause: err}
    }
    if rec == nil {
        return domain.User{}, &domain.NotFoundError{Resource: "user", ID: strconv.Itoa(int(id))}
    }
    return mapper.RecordToUser(rec)
}
```

### Разбор ошибок в handler'е

```go
user, err := svc.GetByID(ctx, id)
var notFound *domain.NotFoundError
switch {
case errors.As(err, &notFound): writeError(w, 404, "not_found", notFound.Error())
case err != nil:                writeError(w, 503, "storage_unavailable", "")
default:                        writeJSON(w, 200, dto.UserFromDomain(user))
}
```

`errors.As` — единственный способ проверки типа ошибки. `errors.Is` — для sentinel-ошибок (используется редко).

## Чистые функции в ядре

Функции в `domain/`, `service/`, `store/mapper/` — чистые: входные данные → выходные данные. Никакого I/O, никакого глобального состояния.

Зависимости (порты) передаются явно как параметры или через структуру сервиса:

```go
type UserService struct {
    etcd   port.EtcdPort
    clock  port.ClockPort
    random port.RandomPort
}

func NewUserService(etcd port.EtcdPort, clock port.ClockPort, random port.RandomPort) *UserService {
    return &UserService{etcd: etcd, clock: clock, random: random}
}
```

`time.Now()`, `uuid.New()` напрямую в ядре — запрещены. Только через `ClockPort` и `RandomPort`.

## Именование

| Элемент | Стиль | Пример |
|---------|-------|--------|
| Пакет | `lowercase`, одно слово | `domain`, `service`, `adapter` |
| Экспортированный тип | `PascalCase` | `UserService`, `NotFoundError` |
| Экспортированная функция/метод | `PascalCase` | `GetByID`, `Create` |
| Неэкспортированная функция | `camelCase` | `userKey`, `computeNext` |
| Константа | `PascalCase` | `StatusActive`, `NodeRoleCore` |
| Интерфейс (порт) | `PascalCase` + суффикс `Port` | `EtcdPort`, `ClockPort` |
| Адаптер (структура) | `PascalCase` + суффикс `Adapter` | `EtcdAdapter` |
| Сервис (структура) | `PascalCase` + суффикс `Service` | `UserService` |
| Record (структура) | `PascalCase` + суффикс `Record` | `UserRecord` |
| DTO (структура) | суффикс `Request` / `Response` | `CreateUserRequest` |
| ID в имени | аббревиатура заглавными | `GetByID`, `UserID`, `TokenID` |

## Комментарии

Комментарии пишутся только когда **WHY неочевиден**: скрытое ограничение, нетривиальный инвариант, обходной путь специфической проблемы.

Запрещено:
- Комментировать что делает функция (для этого есть имя).
- Писать многострочные doc-комментарии там, где достаточно имени.
- Оставлять `TODO` без issue / ссылки.
- Ссылаться в комментарии на текущую задачу или контекст PR.

## Запрещённые паттерны

- `panic` в бизнес-логике — только при неинициализированных обязательных зависимостях в `main`.
- Глобальные переменные как хранилище состояния сервиса.
- `fmt.Println` / `log.Print` напрямую в `domain/`, `service/`, `store/` — только через `slog` в оболочке.
- `time.Now()`, `uuid.New()` напрямую в ядре — только через порты.
- `interface{}` / `any` без явного обоснования.
- `_ = err` — ошибки не игнорируются молча.
