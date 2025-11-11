# Use a lightweight Nginx base image
FROM nginx:alpine

# Copy the custom Nginx configuration file into the correct location in the container.
# Since the build context is the 'nginx' folder, we can access nginx.conf directly.
COPY nginx.conf /etc/nginx/nginx.conf

# The image is ready to be used as a reverse proxy.
# The base image already includes the necessary ENTRYPOINT/CMD instructions.