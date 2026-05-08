package adapter

import (
	    "fmt"
	    "github.com/SigilGate/SigilGateAPI/internal/port"
	    )

type FakeRandom struct {
	counter int
}

var _ port.RandomPort = (*FakeRandom)(nil)

func NewFakeRandom() *FakeRandom {
	return &FakeRandom{}
}

func (r *FakeRandom) UUID() string {
	r.counter++
	return fmt.Sprintf("00000000-0000-0000-0000-%012d", r.counter)
}
