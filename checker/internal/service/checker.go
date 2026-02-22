package service

import (
    "net/http"
    "time"
    "uptime-checker/internal/domain"
)

type CheckerService struct {
    httpClient *http.Client
}

func NewCheckerService() *CheckerService {
    return &CheckerService{
        httpClient: &http.Client{
            Timeout: 10 * time.Second,
        },
    }
}

func (s *CheckerService) CheckWebsite(url string) *domain.CheckResult {
    start := time.Now()

    resp, err := s.httpClient.Get(url)
    responseTime := time.Since(start).Milliseconds()

    result := &domain.CheckResult{
        ResponseTime: responseTime,
        CheckedAt:    time.Now(),
    }

    if err != nil {
        result.IsUp = false
        result.StatusCode = 0
        return result
    }
    defer resp.Body.Close()

    result.IsUp = resp.StatusCode >= 200 && resp.StatusCode < 300
    result.StatusCode = resp.StatusCode

    return result
}