package main

import (
    "context"
    "database/sql"
    "encoding/json"
    "fmt"
    "log"
    "os"
    "time"

    "github.com/go-redis/redis/v8"
    "github.com/joho/godotenv"
    _ "github.com/lib/pq"
)

type CheckTask struct {
    WebsiteID int    `json:"website_id"`
    URL       string `json:"url"`
    Interval  int    `json:"interval"`
}

type CheckResult struct {
    WebsiteID    int
    StatusCode   int
    ResponseTime int64
    IsUp         bool
    CheckedAt    time.Time
}

var (
    redisClient *redis.Client
    db          *sql.DB
    ctx         = context.Background()
)

func main() {
    // Load env
    if err := godotenv.Load(); err != nil {
        log.Println("No .env file found")
    }

    // Connect to Redis
    redisClient = redis.NewClient(&redis.Options{
        Addr: os.Getenv("REDIS_HOST") + ":6379",
    })

    // Connect to PostgreSQL
    connStr := os.Getenv("DATABASE_URL")
    var err error
    db, err = sql.Open("postgres", connStr)
    if err != nil {
        log.Fatal("Failed to connect to database:", err)
    }
    defer db.Close()

    // Start workers
    for i := 0; i < 5; i++ {
        go worker(i)
    }

    // Keep main thread alive
    select {}
}

func worker(id int) {
    log.Printf("Worker %d started", id)

    for {
        // Get task from Redis queue
        taskJSON, err := redisClient.BLPop(ctx, 0, "check_queue").Result()
        if err != nil {
            log.Printf("Worker %d: Error getting task: %v", id, err)
            continue
        }

        var task CheckTask
        if err := json.Unmarshal([]byte(taskJSON[1]), &task); err != nil {
            log.Printf("Worker %d: Error parsing task: %v", id, err)
            continue
        }

        log.Printf("Worker %d: Checking %s (ID: %d)", id, task.URL, task.WebsiteID)

        // Perform the check
        result := checkWebsite(task.URL)
        result.WebsiteID = task.WebsiteID

        // Save result to database
        if err := saveResult(result); err != nil {
            log.Printf("Worker %d: Error saving result: %v", id, err)
        }

        // If website is down, trigger alert
        if !result.IsUp {
            triggerAlert(task.WebsiteID, task.URL)
        }

        // Schedule next check
        scheduleNextCheck(task)
    }
}

func checkWebsite(url string) CheckResult {
    start := time.Now()

    client := http.Client{
        Timeout: 10 * time.Second,
    }

    resp, err := client.Get(url)
    responseTime := time.Since(start).Milliseconds()

    result := CheckResult{
        ResponseTime: responseTime,
        CheckedAt:    time.Now(),
    }

    if err != nil {
        result.IsUp = false
        result.StatusCode = 0
        log.Printf("Website %s is DOWN: %v", url, err)
    } else {
        defer resp.Body.Close()
        result.IsUp = resp.StatusCode >= 200 && resp.StatusCode < 300
        result.StatusCode = resp.StatusCode
        log.Printf("Website %s is UP (Status: %d, Time: %dms)",
            url, resp.StatusCode, responseTime)
    }

    return result
}

func saveResult(result CheckResult) error {
    query := `
        INSERT INTO check_logs (website_id, status_code, response_time, is_up, checked_at)
        VALUES ($1, $2, $3, $4, $5)
    `

    _, err := db.Exec(query,
        result.WebsiteID,
        result.StatusCode,
        result.ResponseTime,
        result.IsUp,
        result.CheckedAt,
    )

    if err != nil {
        return err
    }

    // Update website's last status
    updateQuery := `
        UPDATE websites
        SET last_status = $1, last_checked = $2
        WHERE id = $3
    `
    _, err = db.Exec(updateQuery, result.IsUp, result.CheckedAt, result.WebsiteID)

    return err
}

func scheduleNextCheck(task CheckTask) {
    // Re-add to queue after interval
    time.AfterFunc(time.Duration(task.Interval)*time.Minute, func() {
        taskJSON, _ := json.Marshal(task)
        redisClient.RPush(ctx, "check_queue", taskJSON)
    })
}

func triggerAlert(websiteID int, url string) {
    // Send to email worker via Redis
    alert := map[string]interface{}{
        "website_id": websiteID,
        "url":        url,
        "timestamp":  time.Now(),
    }

    alertJSON, _ := json.Marshal(alert)
    redisClient.RPush(ctx, "alert_queue", alertJSON)
}