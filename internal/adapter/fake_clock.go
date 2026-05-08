package adapter

import (
	    "time"
		"github.com/SigilGate/SigilGateAPI/internal/port")

type FakeClock struct {
	fixed time.Time
}

var _ port.ClockPort = (*FakeClock)(nil)

func NewFakeClock(t time.Time) *FakeClock {
	return &FakeClock{fixed: t}
}

func (c *FakeClock) Now() time.Time {
	return c.fixed
}
