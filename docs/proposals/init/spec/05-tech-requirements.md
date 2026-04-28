# 05. Технические требования

## Язык и среда выполнения

- **Go 1.22+** — обязательный минимум. Используется: range over integers (`for range N`), structured logging (`log/slog` из stdlib).
- **Операционная система:** Linux (Debian 12, Debian 13, Ubuntu 22, Ubuntu 24). Минимальный по размеру Docker image. Поддержка macOS не является целью.

## Зависимости

Принцип: stdlib приоритетнее внешней зависимости. Внешняя зависимость добавляется только когда stdlib не решает задачу. Каждая зависимость должна быть обоснована.

### Обязательные

| Модуль | Обоснование |
|--------|-------------|
| `github.com/go-chi/chi/v5` | HTTP-роутер. stdlib `net/http` не имеет параметров пути и middleware-цепочек. chi — минимальная stdlib-совместимая обёртка. |
| `go.etcd.io/etcd/client/v3` | Официальный Go-клиент к etcd v3 (gRPC + mTLS). Нет альтернативы. |

### Для разработки / тестирования

| Модуль | Обоснование |
|--------|-------------|
| `github.com/stretchr/testify` | `assert` и `require` — устраняют boilerplate в тестах без магии. |

### Явно не используются

- `github.com/spf13/viper` — конфигурация через `os.Getenv`, viper избыточен без CLI.
- `github.com/spf13/cobra` — CLI не входит в состав этого проекта.
- `github.com/gin-gonic/gin` — выбран chi как stdlib-совместимый роутер.
- `github.com/go-playground/validator` — валидация реализована вручную в сервисном слое.
- ORM-библиотеки — хранилище etcd, не SQL.

## Контейнеризация

### Production

Многоэтапная сборка — финальный образ не содержит Go-тулчейна:

```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o sigilgateapp ./cmd/sigilgateapp

FROM gcr.io/distroless/static-debian12
COPY --from=builder /app/sigilgateapp /sigilgateapp
ENTRYPOINT ["/sigilgateapp"]
```

- Финальный образ — `distroless/static`: нет shell, нет пакетного менеджера, минимальная поверхность атаки.
- Статический бинарь (`CGO_ENABLED=0`) — нет зависимостей на libc.
- Секреты (etcd mTLS certs) монтируются как K8s Secrets, не запекаются в образ.
- Конфигурация — env vars.
- Пользователь без root прав (distroless использует nonroot по умолчанию).
- Слушает только `127.0.0.1:8000` — трафик снаружи принимает nginx sidecar.

### nginx sidecar

Отдельный контейнер в том же Pod — обеспечивает TLS termination.

- Образ: `nginx:stable-alpine`
- Конфигурация nginx монтируется как ConfigMap
- Порт `:443` — внешний HTTPS
- Порт `:80` — только ACME http-01 challenge
- `proxy_pass http://127.0.0.1:8000`

**certbot** — отдельный K8s `CronJob` (образ `certbot/certbot`):
- Монтирует тот же PVC с сертификатами
- Запускается по расписанию: `0 3 * * *`
- После renewal — делает `nginx -s reload`

**PersistentVolumeClaim** (`/etc/letsencrypt`) монтируется в:
- nginx sidecar (чтение сертификата)
- CronJob certbot (обновление сертификата)

### Тесты (Dockerfile.test)

Отдельный образ для тестов:
- Базовый образ `golang:1.22-alpine` со всеми зависимостями.
- Интеграционные тесты запускают etcd как sidecar через `docker compose`.
- Все тесты запускаются только через `./run_tests.sh`.

Локальный запуск (`go test ./...`) **не допустим**. Единственный канонический способ запуска — контейнерный.

## K8s манифесты

Располагаются в `deploy/`:

```
deploy/
├── deployment.yaml       ← Pod с двумя контейнерами: sigilgateapp + nginx
├── service.yaml          ← NodePort Service :443 и :80 (для ACME)
├── configmap-nginx.yaml  ← конфиг nginx (server block, proxy_pass, TLS)
├── pvc.yaml              ← PersistentVolumeClaim для /etc/letsencrypt
├── cronjob-certbot.yaml  ← CronJob для renewal сертификата
└── secret.yaml           ← шаблон; реальные секреты создаются вручную, не в репо
```

### Readiness probe

```
GET /health → 200 {"status": "ok", "etcd": "ok"}
```

Если etcd недоступен — `/health` возвращает `503`. K8s исключит pod из балансировки.

### Resource limits

```yaml
# sigilgateapp container
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 200m
    memory: 128Mi

# nginx container
resources:
  requests:
    cpu: 20m
    memory: 32Mi
  limits:
    cpu: 100m
    memory: 64Mi
```

## Конфигурация

Все параметры через env vars. Валидация при старте — если обязательная переменная отсутствует, приложение завершается с понятным сообщением.

```
SIGILGATEAPP_ETCD_ENDPOINTS   ← обязательно; comma-separated URLs
SIGILGATEAPP_ETCD_CA_CERT     ← обязательно; путь к CA cert
SIGILGATEAPP_ETCD_CLIENT_CERT ← обязательно; путь к client cert
SIGILGATEAPP_ETCD_CLIENT_KEY  ← обязательно; путь к client key
SIGILGATEAPP_HOST             ← 127.0.0.1 (default)
SIGILGATEAPP_PORT             ← 8000 (default)
SIGILGATEAPP_LOG_LEVEL        ← info (default)
```

## Логирование

- `log/slog` из stdlib — structured logging без внешних зависимостей.
- Формат: JSON в production (`slog.NewJSONHandler`), текст в development (`slog.NewTextHandler`).
- Уровни: `DEBUG`, `INFO`, `WARN`, `ERROR`.
- Каждый запрос логируется через middleware: метод, путь, статус, latency, `token_id` (не сам токен).

## Версионирование

- Версия задаётся через `go build -ldflags "-X main.version=x.y.z"` в CI.
- Доступна через `GET /api/v1/version` и в заголовке ответа `X-App-Version`.
- Формат: `MAJOR.MINOR.PATCH` (SemVer). До v1.0 — нет гарантий обратной совместимости API.
