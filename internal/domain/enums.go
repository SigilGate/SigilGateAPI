package domain

type Status string

const (
	StatusActive   Status = "active"
	StatusInactive Status = "inactive"
	StatusArchived Status = "archived"
)

type NodeRole string

const (
	NodeRoleCore  NodeRole = "core"
	NodeRoleEntry NodeRole = "entry"
	NodeRoleMgmt  NodeRole = "mgmt"
)

func ParseStatus(s string) (Status, error) {
	st := Status(s)
	switch st {
	case StatusActive, StatusInactive, StatusArchived:
		return st, nil
	}
	return "", &ValidationError{
		Field:   "status",
		Message: "unrecognized status: " + s,
	}
}

func ParseNodeRole(s string) (NodeRole, error) {
	nr := NodeRole(s)
	switch nr {
	case NodeRoleCore, NodeRoleEntry, NodeRoleMgmt:
		return nr, nil
	}
	return "", &ValidationError{
		Field:   "role",
		Message: "unrecognized node role: " + s,
	}
}
