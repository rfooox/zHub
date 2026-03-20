package models

import (
	"database/sql"
	"log"
	"os"
	"sync"
	"time"
)

var (
	db   *sql.DB
	once sync.Once
)

const DBPath = "./data/zhub.db"

func InitDB() {
	once.Do(func() {
		if err := os.MkdirAll("./data", 0755); err != nil {
			log.Fatal("Failed to create data directory:", err)
		}

		var err error
		db, err = sql.Open("sqlite3", DBPath+"?_foreign_keys=on")
		if err != nil {
			log.Fatal("Failed to open database:", err)
		}

		if err = db.Ping(); err != nil {
			log.Fatal("Failed to ping database:", err)
		}

		createTables()
	})
}

func createTables() {
	_, err := db.Exec(`
		CREATE TABLE IF NOT EXISTS resources (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name VARCHAR(100) NOT NULL,
			url VARCHAR(500) NOT NULL,
			category VARCHAR(50) NOT NULL DEFAULT 'other',
			group_name VARCHAR(100) DEFAULT '',
			tags VARCHAR(200) DEFAULT '',
			description TEXT DEFAULT '',
			is_enabled INTEGER DEFAULT 1,
			consul_enabled INTEGER DEFAULT 0,
			consul_check_type VARCHAR(20) DEFAULT 'http',
			consul_check_interval VARCHAR(20) DEFAULT '30s',
			consul_tags VARCHAR(200) DEFAULT '',
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
			updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
		)
	`)
	if err != nil {
		log.Fatal("Failed to create resources table:", err)
	}

	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS resource_status (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			resource_id INTEGER NOT NULL,
			status VARCHAR(20) NOT NULL,
			response_time FLOAT DEFAULT 0,
			checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE
		)
	`)
	if err != nil {
		log.Fatal("Failed to create resource_status table:", err)
	}

	_, err = db.Exec(`CREATE INDEX IF NOT EXISTS idx_resource_category ON resources(category)`)
	if err != nil {
		log.Fatal("Failed to create index:", err)
	}

	_, err = db.Exec(`CREATE INDEX IF NOT EXISTS idx_status_resource ON resource_status(resource_id)`)
	if err != nil {
		log.Fatal("Failed to create index:", err)
	}
}

func CloseDB() {
	if db != nil {
		db.Close()
	}
}

type Resource struct {
	ID                  int64  `json:"id"`
	Name                string `json:"name"`
	URL                 string `json:"url"`
	Category            string `json:"category"`
	GroupName           string `json:"group_name"`
	Tags                string `json:"tags"`
	Description         string `json:"description"`
	IsEnabled           bool   `json:"is_enabled"`
	ConsulEnabled       bool   `json:"consul_enabled"`
	ConsulCheckType     string `json:"consul_check_type"`
	ConsulCheckInterval string `json:"consul_check_interval"`
	ConsulTags          string `json:"consul_tags"`
	CreatedAt           string `json:"created_at"`
	UpdatedAt           string `json:"updated_at"`
}

type ResourceStatus struct {
	ID           int64   `json:"id"`
	ResourceID   int64   `json:"resource_id"`
	Status       string  `json:"status"`
	ResponseTime float64 `json:"response_time"`
	CheckedAt    string  `json:"checked_at"`
}

type CreateResourceRequest struct {
	Name                string `json:"name"`
	URL                 string `json:"url"`
	Category            string `json:"category"`
	GroupName           string `json:"group_name"`
	Tags                string `json:"tags"`
	Description         string `json:"description"`
	IsEnabled           bool   `json:"is_enabled"`
	ConsulEnabled       bool   `json:"consul_enabled"`
	ConsulCheckType     string `json:"consul_check_type"`
	ConsulCheckInterval string `json:"consul_check_interval"`
	ConsulTags          string `json:"consul_tags"`
}

type Stats struct {
	Total           int     `json:"total"`
	Online          int     `json:"online"`
	Offline         int     `json:"offline"`
	AvgResponseTime float64 `json:"avg_response_time"`
}

func GetAllResources(category, group, search string, enabledOnly bool) ([]Resource, error) {
	sql := "SELECT * FROM resources WHERE 1=1"
	var args []interface{}

	if category != "" {
		sql += " AND category = ?"
		args = append(args, category)
	}
	if group != "" {
		sql += " AND group_name = ?"
		args = append(args, group)
	}
	if search != "" {
		sql += " AND (name LIKE ? OR url LIKE ? OR description LIKE ?)"
		pattern := "%" + search + "%"
		args = append(args, pattern, pattern, pattern)
	}
	if enabledOnly {
		sql += " AND is_enabled = 1"
	}
	sql += " ORDER BY category, group_name, name"

	rows, err := db.Query(sql, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var resources []Resource
	for rows.Next() {
		var r Resource
		var isEnabled, consulEnabled int
		err := rows.Scan(
			&r.ID, &r.Name, &r.URL, &r.Category, &r.GroupName, &r.Tags,
			&r.Description, &isEnabled, &consulEnabled,
			&r.ConsulCheckType, &r.ConsulCheckInterval, &r.ConsulTags,
			&r.CreatedAt, &r.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}
		r.IsEnabled = isEnabled == 1
		r.ConsulEnabled = consulEnabled == 1
		resources = append(resources, r)
	}
	return resources, nil
}

func GetResourceByID(id int64) (*Resource, error) {
	var r Resource
	var isEnabled, consulEnabled int
	err := db.QueryRow(`
		SELECT id, name, url, category, group_name, tags, description, 
		       is_enabled, consul_enabled, consul_check_type, consul_check_interval, consul_tags,
		       created_at, updated_at
		FROM resources WHERE id = ?`, id).Scan(
		&r.ID, &r.Name, &r.URL, &r.Category, &r.GroupName, &r.Tags,
		&r.Description, &isEnabled, &consulEnabled,
		&r.ConsulCheckType, &r.ConsulCheckInterval, &r.ConsulTags,
		&r.CreatedAt, &r.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}
	r.IsEnabled = isEnabled == 1
	r.ConsulEnabled = consulEnabled == 1
	return &r, nil
}

func CreateResource(req *CreateResourceRequest) (int64, error) {
	isEnabled := 0
	if req.IsEnabled {
		isEnabled = 1
	}
	consulEnabled := 0
	if req.ConsulEnabled {
		consulEnabled = 1
	}

	if req.ConsulCheckType == "" {
		req.ConsulCheckType = "http"
	}
	if req.ConsulCheckInterval == "" {
		req.ConsulCheckInterval = "30s"
	}

	result, err := db.Exec(`
		INSERT INTO resources (name, url, category, group_name, tags, description, 
		                       is_enabled, consul_enabled, consul_check_type, consul_check_interval, consul_tags)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		req.Name, req.URL, req.Category, req.GroupName, req.Tags, req.Description,
		isEnabled, consulEnabled, req.ConsulCheckType, req.ConsulCheckInterval, req.ConsulTags,
	)
	if err != nil {
		return 0, err
	}
	return result.LastInsertId()
}

func UpdateResource(id int64, req *CreateResourceRequest) error {
	isEnabled := 0
	if req.IsEnabled {
		isEnabled = 1
	}
	consulEnabled := 0
	if req.ConsulEnabled {
		consulEnabled = 1
	}

	_, err := db.Exec(`
		UPDATE resources SET 
			name = ?, url = ?, category = ?, group_name = ?, tags = ?, description = ?,
			is_enabled = ?, consul_enabled = ?, consul_check_type = ?, consul_check_interval = ?, consul_tags = ?,
			updated_at = ?
		WHERE id = ?`,
		req.Name, req.URL, req.Category, req.GroupName, req.Tags, req.Description,
		isEnabled, consulEnabled, req.ConsulCheckType, req.ConsulCheckInterval, req.ConsulTags,
		time.Now().Format("2006-01-02 15:04:05"), id,
	)
	return err
}

func DeleteResource(id int64) error {
	_, err := db.Exec("DELETE FROM resources WHERE id = ?", id)
	return err
}

func GetLatestStatus(resourceID int64) (*ResourceStatus, error) {
	var s ResourceStatus
	err := db.QueryRow(`
		SELECT id, resource_id, status, response_time, checked_at
		FROM resource_status
		WHERE resource_id = ?
		ORDER BY checked_at DESC
		LIMIT 1`, resourceID).Scan(&s.ID, &s.ResourceID, &s.Status, &s.ResponseTime, &s.CheckedAt)
	if err != nil {
		return nil, err
	}
	return &s, nil
}

func SaveStatus(resourceID int64, status string, responseTime float64) error {
	_, err := db.Exec(`
		INSERT INTO resource_status (resource_id, status, response_time, checked_at)
		VALUES (?, ?, ?, ?)`,
		resourceID, status, responseTime, time.Now().Format("2006-01-02 15:04:05"),
	)
	return err
}

func GetStats() (*Stats, error) {
	var stats Stats

	err := db.QueryRow("SELECT COUNT(*) FROM resources WHERE is_enabled = 1").Scan(&stats.Total)
	if err != nil {
		return nil, err
	}

	rows, err := db.Query(`
		SELECT COUNT(DISTINCT rs.resource_id) as online
		FROM resource_status rs
		INNER JOIN resources r ON r.id = rs.resource_id
		WHERE r.is_enabled = 1 
		AND rs.status = 'online'
		AND rs.checked_at = (
			SELECT MAX(checked_at) FROM resource_status WHERE resource_id = rs.resource_id
		)
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	if rows.Next() {
		rows.Scan(&stats.Online)
	}

	stats.Offline = stats.Total - stats.Online

	err = db.QueryRow(`
		SELECT AVG(response_time) FROM resource_status
		WHERE status = 'online' AND checked_at > datetime('now', '-1 hour')
	`).Scan(&stats.AvgResponseTime)
	if err != nil && err != sql.ErrNoRows {
		return nil, err
	}

	return &stats, nil
}

func GetCategories() ([]string, error) {
	rows, err := db.Query("SELECT DISTINCT category FROM resources WHERE category != '' ORDER BY category")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var categories []string
	for rows.Next() {
		var cat string
		if err := rows.Scan(&cat); err != nil {
			return nil, err
		}
		categories = append(categories, cat)
	}
	return categories, nil
}

func GetGroups() ([]string, error) {
	rows, err := db.Query("SELECT DISTINCT group_name FROM resources WHERE group_name != '' ORDER BY group_name")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var groups []string
	for rows.Next() {
		var g string
		if err := rows.Scan(&g); err != nil {
			return nil, err
		}
		groups = append(groups, g)
	}
	return groups, nil
}
