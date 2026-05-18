package v2

type APRSStats struct {
	TotalStations int `json:"total_stations"`
	Stations24h   int `json:"stations_24h"`
	TotalPackets  int `json:"total_packets"`
	Packets24h    int `json:"packets_24h"`
}
