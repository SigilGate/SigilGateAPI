package domain

import "time"

type User struct {
    ID             UserID
    Username       string
    Status         Status
    StatusAt       time.Time
    HashTelegramID *string
    CreatedAt      time.Time
    CoreNodes      []NodeIP
}

type Device struct {
    UUID      DeviceUUID
    UserID    UserID
    Name      string
    Status    Status
    StatusAt  time.Time
    CreatedAt time.Time
    CoreNode  *NodeIP
}

type Node struct {
    IP                NodeIP
    Role              NodeRole
    Domain            *string
    ClientServiceName *string
    CoreServiceName   *string
    CellDomain        *CellDomain
    NodeNumber        *int
    UUID              *string
    Status            Status
    StatusAt          time.Time
}

type Cell struct {
    Domain   CellDomain
    Status   Status
    StatusAt time.Time
}

type Route struct {
    UUID     DeviceUUID
    CoreIP   NodeIP
    Status   Status
    StatusAt time.Time
}

type JoinToken struct {
    Token          string
    CreatedAt      time.Time
    ExpiredAt      time.Time
    Used           bool
    CellDomain     CellDomain
    NodeNumber     int
    AssignedDomain string // "{NodeNumber}.core.{CellDomain}"
}
