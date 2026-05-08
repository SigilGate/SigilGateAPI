package adapter

import (
	"context"
	"github.com/SigilGate/SigilGateAPI/internal/port"
	"strings"
    "sync"
)

type InMemoryETCD struct {
	mu sync.Mutex
	store map[string]string
}

var _ port.EtcdPort = (*InMemoryETCD)(nil)

func NewInMemoryETCD() *InMemoryETCD {
	return &InMemoryETCD{store: make(map[string]string)}
}

func (e *InMemoryETCD) Get(_ context.Context, key string) (*string, error) {
	e.mu.Lock()
	defer e.mu.Unlock()
	
	v, ok :=  e.store[key]
	if !ok {
		return nil, nil
	}
	return &v, nil
}

func (e *InMemoryETCD) Put(_ context.Context, key, value string) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	e.store[key] = value
	return nil
}

func (e *InMemoryETCD) Delete(_ context.Context, key string) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	delete(e.store, key)
	return nil
}

func (e *InMemoryETCD) PrefixScan(_ context.Context, prefix string) (map[string]string, error) {
	e.mu.Lock()
	defer e.mu.Unlock()

    m := make(map[string]string)
	for k, v := range e.store {
		if strings.HasPrefix(k, prefix) {
			m[k] = v
		}
	}
	return m, nil
}

func (e *InMemoryETCD) Txn(_ context.Context, ops []port.TxnOp) error {
	e.mu.Lock()
	defer e.mu.Unlock()
	for _, op := range ops {
		if op.Value==nil {
			delete(e.store, op.Key)
		} else {
			e.store[op.Key] = *op.Value
		}
	}
	return nil
}

func (e *InMemoryETCD) CompareAndSwap(_ context.Context, key string, expected *string, value string) (bool, error) {
	e.mu.Lock()
	defer e.mu.Unlock()

    current, exists := e.store[key]
	if expected==nil {
		if exists {
			return false, nil
		}
	} else {
		if !exists || current != *expected {
			return false, nil
		}
	}
    e.store[key] = value
	return true, nil
}
