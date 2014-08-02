# Database connection config
# The URI most scrapers will use to access the DB
DB_URI = 'sqlite:///db/data.sqlite'
# The read-only URI the server will use to access the DB
DB_URI_READ_ONLY = 'file:db/data.sqlite?mode=ro'

# Server performance config
# Max time an SQL query can take before it's killed
QUERY_TIMEOUT_SECS = 2
# How long query results are cached before they're stale
QUERY_CACHE_EXPIRY_SECS = 30

# External services config
# The server's web-visible hostname, NOT including a trailing slash or port
# If you're running this locally, use 'http://localhost'
SERVER_HOST = 'http://localhost'
# The port on which Narcissa will answer web SQL queries
SERVER_PORT = 20410
