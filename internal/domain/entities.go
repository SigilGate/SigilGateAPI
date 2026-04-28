package domain

import "time"

type User struct {
    ID             UserID
    Username       string
    Status         Status
    StatusAt       time.Time
    HashTelegramID *string
    Created      time.Time
    CoreNodes      []NodeIP
}

type Device struct {
    UUID      DeviceUUID
    UserID    UserID
    Name      string
    Status    Status
    StatusAt  time.Time
    Created time.Time
    CoreNode  *NodeIP
}

type Node struct {
    IP                NodeIP
    Role              NodeRole
    Status            Status
    StatusAt          time.Time
    Domain            *string
    CellDomain        *CellDomain
    NodeNumber        *int
    UUID              *string
    ClientServiceName *string
    CoreServiceName   *string
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

type APIToken struct {
    TokenID    TokenID
    Name       string
    TokenHash  string
    Created    time.Time
    Active     bool
    LastUsedAt time.Time
}
