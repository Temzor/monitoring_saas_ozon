package domain

import "time"

type Website struct {
    ID            int
    URL           string
    Name          string
    CheckInterval int
    LastStatus    bool
    LastChecked   *time.Time
    OwnerID       int
}

type CheckResult struct {
    WebsiteID    int
    StatusCode   int
    ResponseTime int64
    IsUp         bool
    CheckedAt    time.Time
}

type CheckTask struct {
    WebsiteID int
    URL       string
    Interval  int
}