FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 4566
EXPOSE 4566

# Start nginx
CMD ["nginx", "-g", "daemon off;"]