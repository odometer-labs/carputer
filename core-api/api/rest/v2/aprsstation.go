package v2

import "time"

type APRSStation struct {
	Callsign    string    `json:"callsign"`
	SymbolTable string    `json:"symbol_table"`
	SymbolCode  string    `json:"symbol_code"`
	LastComment *string   `json:"last_comment"`
	LastSeen    time.Time `json:"last_seen"`
	Latitude    float64   `json:"latitude"`
	Longitude   float64   `json:"longitude"`
	DistanceM   *float64  `json:"distance_m"`
	PacketCount int       `json:"packet_count"`
}
