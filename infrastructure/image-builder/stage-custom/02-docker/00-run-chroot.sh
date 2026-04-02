
#!/bin/bash -e

curl -fsSL https://get.docker.com | sh
usermod -aG docker $FIRST_USER_NAME