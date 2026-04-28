package domain

type Status string

const (
	StatusActive    Status = "active"
	StatusInactive  Status = "inactive"
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
		return Status, nil
	}
	return "", &ValidadionError{
		Field:   "status",
		Message: "Unrecognized status: " + s}
}

func ParseNodeRole(s string) (NodeRole, error) {
	switch NodeRole(s) {
	case NodeRoleCore, NodeRoleEntry, NodeRoleMgmt:
		return NodeRole, nil
	}
	return "", &ValidationError{
		Field:   "Node role",
		Message: "Unrecognized node role: " + s}
}
