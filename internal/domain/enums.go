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
	switch Status(s) {
	case StatusActive, StatusInactive, StatusArchived:
		return Status(s), nil
	}
	return "", &ValidationError{
		Field:   "status",
		Message: "Unrecognized status: " + s,
	}
}

func ParseNodeRole(s string) (NodeRole, error) {
	switch NodeRole(s) {
	case NodeRoleCore, NodeRoleEntry, NodeRoleMgmt:
		return NodeRole(s), nil
	}
	return "", &ValidationError{
		Field:   "node_role",
		Message: "Unrecognized node role: " + s,
	}
}
