package v2

type ImportTrackPointRequest struct {
	TrackID uint64 `path:"track_id"`
	Body    TrackPoint
}

type ImportTrackPointResponse struct{}
