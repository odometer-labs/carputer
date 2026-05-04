Installation and Setup:
//To be updated when database is up and running
NEEDS PostGIS EXTENSION INSTALLED

### 📐 Technical Specifications
* **Coordinate System**: WGS84 (EPSG:4326) using the `GEOGRAPHY` type for high-precision global calculations.
* **Units of Measure**: 
    * **Distance**: Meters (standardized by PostGIS Geography).
    * **Speed**: Meters per second (MPS).
    * **Heading**: Degrees (0-360, where 0 is True North).
        * **New Road Differentiation**: 30 meters - swallows gps errors/drifts and able to distinguish different roads
* **Spatial Indexing**: GIST (Generalized Search Tree) indexes are applied to all `geom` columns to ensure $O(\log n)$ 
lookup performance for proximity queries.

---------------------------------------------------------------------------------------------------------------
Database Schema
All objects are encapsulated within the `gps` schema for modularity.

---------------------------------------------------------------------------------------------------------------
Tables:
`gps.tracks`: Metadata for recording sessions (start/end) times

`gps.track_points`: Raw telemetry data (lat/long, speed, heading, timestamp)

`gps.track_lines`: Pre-computed LINESTRING geometries for high-performance mapping. 

---------------------------------------------------------------------------------------------------------------
CRUD Operations

Standard operations to manage your tracking data:

### Session Lifecycle
`gps.create_track()`: Starts a new track and generates name or returns the active track_id.
`gps.create_track(name)`: Starts a new track with specificed name or returns the active track_id.

`gps.add_track_point(...)`: Ingests raw GPS coordinates.

`gps.end_track()`: Ends the current session.

### Data Management

`gps.retrieve_track(id)`: Fetches a specific track's metadata and geometry as GEOJSON.
`gps.view_all_tracks()`: Fetches all tracks' metadata and geometry as GEOJSON.

`gps.update_track(...)`: Modifies existing track metadata (start/end time, name).
`gps.delete_track(id)`: Removes a track and all associated spatial data (cascading)

`gps.import_track()`: Creates a new track and track line using a GEOJSON text string.

`gps.get_tracks_mvt(...)`: Retrieval track function with 4 modes that return a mapbox vector tile: 
                            -- CAN ONLY RETRIEVE TRACKS IN SPECIFIED TILE ENVELOPE
                                -- `z,x,y` = 0,0,0 for `whole world`
                                    --- `0,0,0 causes nearby mode to malfunction`
                            - All: Retrieves all tracks in specified tile envelope
                            - Single: Retrieves track by specified track_id in specified tile envelope
                            - Nearby: Retrieves all nearby tracks within specified meters in specified tile envelope
                            - Road: Retrieves all tracks that overlap with current track in specified tile envelope

---------------------------------------------------------------------------------------------------------------
Spatial Analysis Queries
Advanced PostGIS-driven logic for real-time discovery and historical analysis.

`gps.is_new_road()`: Returns TRUE if the current position is `> 30m` from any previous tracks.

`gps.get_track_lines_near_location(meters)`: Finds all historical tracks within a specific radius of the current user, as GEOJSON.

`gps.get_track_lines_using_road()`: Identifies historical tracks that overlap with the current active path, as GEOJSON.

---------------------------------------------------------------------------------------------------------------
Utilities

`gps.validate_geometry(track_id)`: Validates and fixes spatial geometry.

`gps.get_latest_track_point()`: Quick-access helper for last inserted telemetry data

---------------------------------------------------------------------------------------------------------------

### Database Only (Not required for application)
This system uses a PostgreSQL Trigger (`trg_update_track_line`) to manage spatial data automatically after each raw telemetry data insert.

