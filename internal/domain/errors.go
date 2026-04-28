package domain

import (
        "fmt"
        "time"
)

type NotFoundError struct {
	Resource string
	ID       string
}

func (e *NotFoundError) Error() string {
	return fmt.Sprintf("%s %s not found", e.Resource, e.ID)
}

type AlreadyExistsError struct {
	Resource string
	ID       string
}

func (e *AlreadyExistsError) Error() string {
	return fmt.Sprintf("%s %s already exists", e.Resource, e.ID)
}

type ValidationError struct {
	Field   string
	Message string
}

func (e *ValidationError) Error() string {
	return fmt.Sprintf("validation error on field %q: %s", e.Field, e.Message)
}

type EtcdError struct {
	Message string
}

func (e *EtcdError) Error() string {
	return fmt.Sprintf("ETCD storage error: %s", e.Message)
}

type TokenExpiredError struct {
	Token     string
	ExpiredAt time.Time
}

func (e *TokenExpiredError) Error() string {
	return fmt.Sprintf("token %s was expired at %v", e.Token, e.ExpiredAt)
}

type TokenConsumedError struct {
	Token string
}

func (e *TokenConsumedError) Error() string {
	return fmt.Sprintf("token %s has already been consumed", e.Token)
}
