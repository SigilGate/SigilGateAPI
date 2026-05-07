package port

import "time"

type ClockPort interface {
	Now() time.Time
}
