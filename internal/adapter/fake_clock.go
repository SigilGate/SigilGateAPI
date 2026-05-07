package fake_clock

import "time"

type FakeClock struct {
	fixed time.Time
}

func NewFakeClock(t time.Time) *FakeClock {
	return &FakeClock{fixed: t}
}

func (c *FakeClock) Now() time.Time {
	return c.fixed
}
