package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math"
	"net/http"
	"time"

	"github.com/gorilla/websocket"
	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/host"
	"github.com/shirou/gopsutil/v3/load"
	"github.com/shirou/gopsutil/v3/mem"
	psnet "github.com/shirou/gopsutil/v3/net"
)

type CPUStats struct {
	PercentTotal   float64   `json:"percent_total"`
	PercentPerCore []float64 `json:"percent_per_core"`
	LoadAvg1       float64   `json:"load_avg_1"`
	LoadAvg5       float64   `json:"load_avg_5"`
	LoadAvg15      float64   `json:"load_avg_15"`
}

type MemStats struct {
	TotalBytes     uint64  `json:"total_bytes"`
	UsedBytes      uint64  `json:"used_bytes"`
	AvailableBytes uint64  `json:"available_bytes"`
	CachedBytes    uint64  `json:"cached_bytes"`
	FreeBytes      uint64  `json:"free_bytes"`
	UsedPercent    float64 `json:"used_percent"`
}

type DiskStats struct {
	TotalBytes  uint64  `json:"total_bytes"`
	UsedBytes   uint64  `json:"used_bytes"`
	FreeBytes   uint64  `json:"free_bytes"`
	UsedPercent float64 `json:"used_percent"`
}

type NetStats struct {
	BytesRecv     uint64 `json:"bytes_recv"`
	BytesSent     uint64 `json:"bytes_sent"`
	RecvRateBytes uint64 `json:"recv_rate_bytes"`
	SendRateBytes uint64 `json:"send_rate_bytes"`
}

type SysHealth struct {
	UptimeSeconds uint64    `json:"uptime_seconds"`
	CPU           CPUStats  `json:"cpu"`
	Memory        MemStats  `json:"memory"`
	Disk          DiskStats `json:"disk"`
	Network       NetStats  `json:"network"`
}

var (
	upgrader    = websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }}
	prevNet     *psnet.IOCountersStat
	prevNetTime time.Time
)

func round2(f float64) float64 {
	return math.Round(f*100) / 100
}

func roundSlice(fs []float64) []float64 {
	out := make([]float64, len(fs))
	for i, f := range fs {
		out[i] = round2(f)
	}
	return out
}

func collectStats() (*SysHealth, error) {
	uptime, err := host.Uptime()
	if err != nil {
		return nil, fmt.Errorf("uptime: %w", err)
	}

	cpuTotal, err := cpu.Percent(0, false)
	if err != nil || len(cpuTotal) == 0 {
		return nil, fmt.Errorf("cpu total: %w", err)
	}
	cpuPerCore, err := cpu.Percent(0, true)
	if err != nil {
		return nil, fmt.Errorf("cpu per-core: %w", err)
	}

	avg, err := load.Avg()
	if err != nil {
		return nil, fmt.Errorf("load avg: %w", err)
	}

	vmStat, err := mem.VirtualMemory()
	if err != nil {
		return nil, fmt.Errorf("memory: %w", err)
	}

	diskStat, err := disk.Usage("/")
	if err != nil {
		return nil, fmt.Errorf("disk: %w", err)
	}

	netStats, err := psnet.IOCounters(false)
	if err != nil || len(netStats) == 0 {
		return nil, fmt.Errorf("net: %w", err)
	}
	current := netStats[0]
	now := time.Now()

	var recvRate, sendRate uint64
	if prevNet != nil && current.BytesRecv >= prevNet.BytesRecv && current.BytesSent >= prevNet.BytesSent {
		elapsed := now.Sub(prevNetTime).Seconds()
		if elapsed > 0 {
			recvRate = uint64(float64(current.BytesRecv-prevNet.BytesRecv) / elapsed)
			sendRate = uint64(float64(current.BytesSent-prevNet.BytesSent) / elapsed)
		}
	}
	prevNet = &current
	prevNetTime = now

	return &SysHealth{
		UptimeSeconds: uptime,
		CPU: CPUStats{
			PercentTotal:   round2(cpuTotal[0]),
			PercentPerCore: roundSlice(cpuPerCore),
			LoadAvg1:       round2(avg.Load1),
			LoadAvg5:       round2(avg.Load5),
			LoadAvg15:      round2(avg.Load15),
		},
		Memory: MemStats{
			TotalBytes:     vmStat.Total,
			UsedBytes:      vmStat.Used,
			AvailableBytes: vmStat.Available,
			CachedBytes:    vmStat.Cached,
			FreeBytes:      vmStat.Free,
			UsedPercent:    round2(vmStat.UsedPercent),
		},
		Disk: DiskStats{
			TotalBytes:  diskStat.Total,
			UsedBytes:   diskStat.Used,
			FreeBytes:   diskStat.Free,
			UsedPercent: round2(diskStat.UsedPercent),
		},
		Network: NetStats{
			BytesRecv:     current.BytesRecv,
			BytesSent:     current.BytesSent,
			RecvRateBytes: recvRate,
			SendRateBytes: sendRate,
		},
	}, nil
}

func wsHandler(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("upgrade: %v", err)
		return
	}
	defer conn.Close()

	ticker := time.NewTicker(time.Second)
	defer ticker.Stop()

	for range ticker.C {
		stats, err := collectStats()
		if err != nil {
			log.Printf("collect: %v", err)
			continue
		}
		data, err := json.Marshal(stats)
		if err != nil {
			continue
		}
		if err := conn.WriteMessage(websocket.TextMessage, data); err != nil {
			return
		}
	}
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Write([]byte(`{"status":"healthy"}`))
}

func main() {
	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/ws/sys-health", wsHandler)
	log.Println("sys-health listening on :8090")
	log.Fatal(http.ListenAndServe(":8090", nil))
}
