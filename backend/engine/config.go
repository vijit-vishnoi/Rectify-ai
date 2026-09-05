package engine

import (
	"log"
	"os"
	"sync"
	"time"

	"github.com/BurntSushi/toml"
)

type PolicyConfigData struct {
	Guardrails struct {
		MaxRetries    int `toml:"max_retries"`
		MaxAgeDays     int `toml:"max_age_days"`
		RbiNoticeHours int `toml:"rbi_notice_hours"`
	} `toml:"guardrails"`
}

type PolicyConfig struct {
	mu   sync.RWMutex
	Data PolicyConfigData
}

var GlobalConfig = &PolicyConfig{
	Data: PolicyConfigData{},
}

func init() {
	GlobalConfig.Data.Guardrails.MaxRetries = 3
	GlobalConfig.Data.Guardrails.MaxAgeDays = 21
	GlobalConfig.Data.Guardrails.RbiNoticeHours = 24
}

func (c *PolicyConfig) LoadConfig(filePath string) error {
	var newData PolicyConfigData
	if _, err := toml.DecodeFile(filePath, &newData); err != nil {
		return err
	}

	c.mu.Lock()
	defer c.mu.Unlock()
	c.Data = newData
	log.Printf("[CONFIG] Hot-reloaded compliance policies. Max Retries loaded: %d", c.Data.Guardrails.MaxRetries)
	return nil
}

func (c *PolicyConfig) WatchConfig(filePath string) {
	_ = c.LoadConfig(filePath) 

	var lastModTime time.Time
	stat, err := os.Stat(filePath)
	if err == nil {
		lastModTime = stat.ModTime()
	}

	for {
		stat, err := os.Stat(filePath)
		if err == nil {
			modTime := stat.ModTime()
			if !lastModTime.IsZero() && modTime.After(lastModTime) {
				if err := c.LoadConfig(filePath); err != nil {
					log.Printf("[CONFIG ERROR] Failed to hot-reload: %v", err)
				}
			}
			lastModTime = modTime
		}
		time.Sleep(2 * time.Second)
	}
}

