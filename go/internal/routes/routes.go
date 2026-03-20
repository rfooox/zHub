package routes

import (
	"log"
	"net/http"
	"strconv"
	"time"

	"zhub/internal/config"
	"zhub/internal/models"

	"github.com/gin-gonic/gin"
)

var cfg *config.Config

func init() {
	cfg = config.Load()
}

func Register(r *gin.Engine) {
	r.GET("/", index)
	r.GET("/add", addPage)
	r.GET("/edit/:id", editPage)

	api := r.Group("/api")
	{
		api.GET("/resources", getResources)
		api.GET("/resources/:id", getResource)
		api.POST("/resources", createResource)
		api.PUT("/resources/:id", updateResource)
		api.DELETE("/resources/:id", deleteResource)
		api.GET("/categories", getCategories)
		api.GET("/groups", getGroups)

		api.GET("/consul/status", consulStatus)
		api.GET("/consul/services", getConsulServices)
		api.POST("/consul/sync-to-consul", syncToConsul)
		api.POST("/consul/sync-from-consul", syncFromConsul)

		api.GET("/stats", getStats)
		api.POST("/check/:id", checkResource)
	}

	if cfg.HealthCheck.Enabled {
		go healthCheckWorker()
	}
}

func index(c *gin.Context) {
	c.HTML(http.StatusOK, "index.html", nil)
}

func addPage(c *gin.Context) {
	c.HTML(http.StatusOK, "add.html", nil)
}

func editPage(c *gin.Context) {
	id := c.Param("id")
	c.HTML(http.StatusOK, "edit.html", gin.H{"resource_id": id})
}

func getResources(c *gin.Context) {
	category := c.Query("category")
	group := c.Query("group")
	search := c.Query("search")

	resources, err := models.GetAllResources(category, group, search, true)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	result := make([]gin.H, len(resources))
	for i, r := range resources {
		res := gin.H{
			"id":                    r.ID,
			"name":                  r.Name,
			"url":                   r.URL,
			"category":              r.Category,
			"group_name":            r.GroupName,
			"tags":                  r.Tags,
			"description":           r.Description,
			"is_enabled":            r.IsEnabled,
			"consul_enabled":        r.ConsulEnabled,
			"consul_check_type":     r.ConsulCheckType,
			"consul_check_interval": r.ConsulCheckInterval,
			"consul_tags":           r.ConsulTags,
			"created_at":            r.CreatedAt,
			"updated_at":            r.UpdatedAt,
		}

		if cfg.Consul.Enabled {
			status, err := models.GetLatestStatus(r.ID)
			if err == nil && status != nil {
				res["health_status"] = gin.H{
					"status":        status.Status,
					"response_time": status.ResponseTime,
					"checked_at":    status.CheckedAt,
				}
			} else {
				res["health_status"] = nil
			}
		} else {
			res["health_status"] = nil
		}
		result[i] = res
	}

	c.JSON(http.StatusOK, gin.H{"success": true, "data": result})
}

func getResource(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Invalid ID"})
		return
	}

	resource, err := models.GetResourceByID(id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"success": false, "error": "Resource not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true, "data": resource})
}

func createResource(c *gin.Context) {
	var req models.CreateResourceRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Name and URL are required"})
		return
	}

	if req.Name == "" || req.URL == "" {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Name and URL are required"})
		return
	}

	if req.Category == "" {
		req.Category = "other"
	}

	id, err := models.CreateResource(&req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"success": true, "data": gin.H{"id": id}})
}

func updateResource(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Invalid ID"})
		return
	}

	var req models.CreateResourceRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": err.Error()})
		return
	}

	if err := models.UpdateResource(id, &req); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true})
}

func deleteResource(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Invalid ID"})
		return
	}

	if err := models.DeleteResource(id); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true})
}

func getCategories(c *gin.Context) {
	categories, err := models.GetCategories()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true, "data": categories})
}

func getGroups(c *gin.Context) {
	groups, err := models.GetGroups()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true, "data": groups})
}

func consulStatus(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"success": true, "data": gin.H{
		"enabled": cfg.Consul.Enabled,
	}})
}

func getConsulServices(c *gin.Context) {
	if !cfg.Consul.Enabled {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Consul is not enabled"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true, "data": []gin.H{}})
}

func syncToConsul(c *gin.Context) {
	if !cfg.Consul.Enabled {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Consul is not enabled"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true, "data": gin.H{"synced": 0, "failed": []string{}}})
}

func syncFromConsul(c *gin.Context) {
	if !cfg.Consul.Enabled {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Consul is not enabled"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true, "data": gin.H{"synced": 0}})
}

func getStats(c *gin.Context) {
	stats, err := models.GetStats()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true, "data": stats})
}

func checkResource(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Invalid ID"})
		return
	}

	resource, err := models.GetResourceByID(id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"success": false, "error": "Resource not found"})
		return
	}

	start := time.Now()
	resp, err := http.Head(resource.URL)
	responseTime := float64(time.Since(start).Milliseconds())

	status := "offline"
	if err == nil && resp.StatusCode < 500 {
		status = "online"
	}

	models.SaveStatus(id, status, responseTime)

	c.JSON(http.StatusOK, gin.H{"success": true, "data": gin.H{
		"status":        status,
		"response_time": responseTime,
	}})
}

func healthCheckWorker() {
	ticker := time.NewTicker(time.Duration(cfg.HealthCheck.Interval) * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		resources, err := models.GetAllResources("", "", "", true)
		if err != nil {
			log.Printf("Health check error: %v", err)
			continue
		}

		for _, r := range resources {
			go func(resource models.Resource) {
				start := time.Now()
				client := &http.Client{Timeout: time.Duration(cfg.HealthCheck.Timeout) * time.Second}
				resp, err := client.Head(resource.URL)
				responseTime := float64(time.Since(start).Milliseconds())

				status := "offline"
				if err == nil && resp.StatusCode < 500 {
					status = "online"
				}

				models.SaveStatus(resource.ID, status, responseTime)
			}(r)
		}
	}
}
