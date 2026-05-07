package clock

import "time"

type ClockPort interface {
	Now() time.Time
}
