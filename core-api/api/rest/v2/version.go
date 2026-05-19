package v2

import "time"

type Version struct {
	VersionNumber string     `json:"version_number"`
	GitHash       *string    `json:"git_hash" required:"false"`
	ReleaseDate   *time.Time `json:"release_date" required:"false"`
}
