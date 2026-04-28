# 01. Видение

## Назначение

SigilGateApp — плоскость данных сети SigilGate (Arch 2.0). Управляет всеми сущностями, необходимыми для работы сети: пользователи, устройства, маршруты, ячейки, ноды, join-токены, ротация serviceName.

**Ядро приложения — HTTP API.** Все интерфейсы (Telegram-бот, Web UI, операторский CLI) — потребители этого API. Бизнес-логика реализована ровно один раз — в API-сервере.

## Место в Arch 2.0

```
LUKS-флешка оператора
└── Keyholder                        ← PKI, SSH, ноды кластера (системный уровень)

Управляющий кластер (K8s + etcd)
├── SigilGateApp [этот проект]       ← HTTP API, единственная точка записи в etcd
│   ├── /sigilgate/* namespace       ← сетевой слой (ноды, маршруты, устройства)
│   └── /public/* namespace          ← коммуникационный слой (обращения, контакты)
├── Telegram Bot (пользовательский)  ← вызывает SigilGateApp API
├── Keyholder Bot (операторский)     ← вызывает SigilGateApp API
├── Subscription Service             ← читает etcd напрямую (read-only, горячий путь)
└── Entry-поды                       ← читают etcd напрямую (read-only, горячий путь)
```

SigilGateApp — единственный компонент, который **пишет** в etcd. Subscription Service и Entry-поды читают etcd напрямую: это горячий путь (каждое клиентское подключение), прослойка через API недопустима по latency.

## Клиентская модель

```
nginx sidecar (HTTPS :443, Let's Encrypt, Bearer Auth)
    └── SigilGateApp API (K8s Deployment, N реплик, :8000 loopback)
            └── HA etcd (mTLS)

Клиенты API:
    Оператор    → Keyholder Bot        → HTTP API
    Пользователь→ Telegram Bot         → HTTP API
    (будущее)   → Core Registration Service → HTTP API
    (будущее)   → Web UI               → HTTP API
    (будущее)   → Операторский CLI     → HTTP API
```

Операторский CLI — отдельный проект. Не входит в состав SigilGateApp. Работает исключительно через HTTP API.

## Разделение с Keyholder

| Задача | SigilGateApp | Keyholder |
|--------|-------------|-----------|
| Пользователи, устройства | ✓ | — |
| Маршруты (UUID → Core) | ✓ | — |
| Ячейки (Cell), SNI-домены | ✓ | — |
| Join-токены участников | ✓ | — |
| Ротация serviceName | ✓ | — |
| Обращения в поддержку | ✓ | — |
| API для ботов | ✓ | — |
| SSH-ключи, PKI, Root CA | — | ✓ |
| Провизионинг нод кластера | — | ✓ |
| Секреты провайдеров | — | ✓ |
| mTLS-сертификаты нод | — | ✓ |

Ссылки — только в одну сторону: Keyholder может ссылаться на `ip` ноды из etcd. SigilGateApp никогда не ссылается на данные Keyholder.

## Функции Backup в составе SigilGateApp

Dump и Load — это API-эндпоинты, не отдельный сервис. BackupSvc в K8s вызывает их по расписанию:
- `POST /api/v1/backup/dump` — сохраняет snapshot etcd в JSON
- `POST /api/v1/backup/load` — загружает snapshot в etcd (migration, disaster recovery)

Это даёт бесплатный инструмент миграции данных (Arch 1.0 → Arch 2.0) и disaster recovery.

## Модель угроз (кратко)

| Угроза | Парирование |
|--------|-------------|
| Компрометация API-пода | etcd хранит только данные сети, не PKI. Отзыв API-токена пода. |
| Несанкционированный запрос | Bearer token аутентификация. Токены на клиент, не общий секрет. |
| Потеря etcd | HA кластер (кворум из 3 нод) + периодический snapshot в git. |
| Утечка `/public/` данных | Namespace изолирован. Кандидат на отдельный кластер в будущем. |
| DDoS на API | Rate limiting на Ingress уровне. API stateless — горизонтальное масштабирование. |
