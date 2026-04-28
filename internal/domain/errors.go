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
	EtcdErrorMessage string
}

func (e *EtcdError) Error() string {
	return fmt.Sprintf("ETCD storage error: %v", e.EtcdErrorMessage)
}

type TokenExpired struct {
	Token     string
	ExpiredAt time.Time
}

func (e *TokenExpired) Error() string {
	return fmt.Sprintf("token %s was expired at %v", e.Token, e.ExpiredAt)
}

type TokenConsumed struct {
	Token string
}

func (e *TokenConsumed) Error() string {
	return fmt.Sprintf("%s was consumed", e.Token)
}
