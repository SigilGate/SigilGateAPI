#!/bin/bash
set -euo pipefail

MODE=${1:-unit}

docker build -f Dockerfile.test -t sigilgateapi-test .

case "$MODE" in
    unit)
        docker run --rm sigilgateapi-test go test ./internal/... -v -count=1
        ;;
    integration)
        echo "Интеграционные тесты добавляются в Stage 002"
        exit 1
        ;;
    all)
        docker run --rm sigilgateapi-test go test ./... -v -count=1
        ;;
    *)
        echo "Usage: $0 [unit|integration|all]"
        exit 1
        ;;
esac
