FROM mysql:8.0

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Override default entrypoint
ENTRYPOINT ["/entrypoint.sh"]
