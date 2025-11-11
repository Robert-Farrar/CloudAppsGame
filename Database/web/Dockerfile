#use lightweight nginx image to serve static file
FROM nginx:stable-alpine

#remove the default nginx welcome files
RUN rm - rf/user/share/nginx/html/*
# Set the working directory inside the container
WORKDIR /app

# Copying the web application files into the container
# assuming the application code is in the 'web' folder.
COPY . /app


RUN pip install --no-cache-dir -r requirements.txt


# Expose the internal port (8500), which Nginx will proxy to
EXPOSE 8500

#start nginx automatically when the container starts
CMD ["nginx", "-g", "daemon off;"]