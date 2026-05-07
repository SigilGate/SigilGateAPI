package adapter

import "fmt"

type FakeRandom struct {
	counter int
}

func NewFakeRandom() *FakeRandom {
	return &FakeRandom
}

func (r *FakeRandom) UUID() string {
	r.counter++
	return fmt.Sprintf("00000000-0000-0000-0000-%012d", r.counter)
}
