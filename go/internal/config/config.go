package config

import (
	"os"
	"strconv"
)

type Config struct {
	App         AppConfig
	Consul      ConsulConfig
	HealthCheck HealthCheckConfig
}

type AppConfig struct {
	Host string
	Port string
}

type ConsulConfig struct {
	Enabled    bool
	Host       string
	Port       int
	Datacenter string
	Scheme     string
}

type HealthCheckConfig struct {
	Enabled  bool
	Interval int
	Timeout  int
}

func getEnv(key, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}

func getEnvBool(key string, defaultVal bool) bool {
	if val := os.Getenv(key); val != "" {
		return val == "true" || val == "1"
	}
	return defaultVal
}

func getEnvInt(key string, defaultVal int) int {
	if val := os.Getenv(key); val != "" {
		if intVal, err := strconv.Atoi(val); err == nil {
			return intVal
		}
	}
	return defaultVal
}

func Load() *Config {
	return &Config{
		App: AppConfig{
			Host: getEnv("APP_HOST", "0.0.0.0"),
			Port: getEnv("APP_PORT", "5000"),
		},
		Consul: ConsulConfig{
			Enabled:    getEnvBool("CONSUL_ENABLED", true),
			Host:       getEnv("CONSUL_HOST", "127.0.0.1"),
			Port:       getEnvInt("CONSUL_PORT", 8500),
			Datacenter: getEnv("CONSUL_DATACENTER", "dc1"),
			Scheme:     getEnv("CONSUL_SCHEME", "http"),
		},
		HealthCheck: HealthCheckConfig{
			Enabled:  getEnvBool("HEALTH_CHECK_ENABLED", true),
			Interval: getEnvInt("HEALTH_CHECK_INTERVAL", 60),
			Timeout:  getEnvInt("HEALTH_CHECK_TIMEOUT", 5),
		},
	}
}
