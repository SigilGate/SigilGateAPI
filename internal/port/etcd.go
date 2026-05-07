package etcd

import "context"

type EtcdPort interface {
	Get (ctx context.Context, key string) (*string, error)
	Put (ctx context.Context, key string, value string) error
	Delete (ctx context.Context, key string) error
	PrefixScan (ctx context.Context, prefix string) (map[string]string)
	Txn (ctx context.Context, ops []TxnOp) error
	CompareAndSwap (ctx context.Context, key string, expected *string, value string) (bool, error)
}

type TxnOp struct {
	Key string
	Value *string // nil = DELETE
}
