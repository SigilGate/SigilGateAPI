package domain

import (
        "fmt"
        "time"
)

type NotFoundError struct {
	Resourse string
	ID       string
}


func (e *NotFoundError) Error() string {
	return fmt.Sprintf("%s %f not found", e.Resourse, e.ID)
}

type AlreadyExist struct {
	Resourse string
	ID       string
}

func (e *AlreadyExist) Error() string {
	return fmt.Sprintf("%s %f already exists", e.Resourse, e.ID)
}

type ValidationError struct {
	Field    string
	Messsage string
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

func (e *EtcdError) Unwrap() string {
  return e.EtcdErrorMessage
}

type TokenExpired struct {
  Token     string
	ExpiredAt time.Time
}

func (e *TokenExpired) Error() string {
	return fmt.Sprintf("token % was expired at %", e.Token, e.ExpiredAt)
}

type TokenConsumed struct {
	Token string
}

func (e *TokenConsumed) Error() string {
	return fmt.Sprintf("% was consumed", e.Token)
}
