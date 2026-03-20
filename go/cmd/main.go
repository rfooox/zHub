package main

import (
	"log"
	"os"
	"os/exec"
	"sync"

	"zhub/internal/config"
	"zhub/internal/models"
	"zhub/internal/routes"

	"github.com/gin-gonic/gin"
)

var (
	server *gin.Engine
	wg     sync.WaitGroup
)

func main() {
	cfg := config.Load()

	if cfg.Consul.Enabled {
		startConsul(&wg)
	}

	models.InitDB()
	defer models.CloseDB()

	router := gin.Default()
	router.Static("/static", "./static")
	router.LoadHTMLGlob("templates/*")

	routes.Register(router)

	addr := cfg.App.Host + ":" + cfg.App.Port
	log.Printf("Server starting on %s", addr)
	router.Run(addr)
}

func startConsul(wg *sync.WaitGroup) {
	wg.Add(1)
	go func() {
		defer wg.Done()
		log.Println("Starting Consul...")
		cmd := exec.Command("consul", "agent", "-dev", "-ui", "-bind=0.0.0.0", "-client=0.0.0.0")
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		cmd.Run()
	}()
}
