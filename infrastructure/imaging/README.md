
# Imaging Utilities

## Setup script

Script for setting up or updating an existing installation

`./setup_script.sh`

## Carputer Image Builder

Script for building carputer raspi 4b+ images utilizing ([pi-gen](https://github.com/rpi-distro/pi-gen))

More information about how pi-gen works refer can be found in the pi-gen repo linked above

### Building an image

Install all the dependencies listed in the pi-gen readme
```

```

For building the carputer image run the `generate_image.sh` script in this repository which will handle downloading pi-gen creating relevant config options and starting the image build process.

** RUNNING THIS SCRIPT WILL CLEAN ANY EXISTING IMAGES AND RESTART FROM SCRATCH ****

*** This script only works on Debian/Ubuntu based Linux systems ***

The output can be found in the ./pi-gen/distribution/

If attempting to build an image on non arm64 architecture you will need to install following (pi-gen chroots into the generated image and runs arm executables which requires binfmt_misc module support)
```
qemu-efi-aarch64
qemu-user-binfmt
qemu-user-static
```