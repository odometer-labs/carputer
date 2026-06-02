### SETUP
First, if create a new docker volume:  
`docker volume create osm-data`  

Then run this command to download the Oregon map:  
```
docker run \
    -e DOWNLOAD_PBF=https://download.geofabrik.de/north-america/us/oregon-latest.osm.pbf \
    -e DOWNLOAD_POLY=https://download.geofabrik.de/north-america/us/oregon.poly \
    -v osm-data:/data/database/ \
    overv/openstreetmap-tile-server \
    import
```

### Downloading other maps
If you need to download another map, run the following:  
`docker system prune -a --volumes`  
`docker volume rm osm-data`  

Then repeat the steps in the first section, only this time, replace the url links with whatever you want from geofabrik.