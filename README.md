# logmetrics

Stats to return per customer daily
 - Total number successful and failed requests
 - Uptime
 - Average latency
 - median latency
 - p99 latency


 # Tasks
 Populate Local Database:
  - Create a local database and define an appropriate schema. Can be anything you like (SQL or NoSQL).
  - Write a script to read api_requests.log, process it and insert the results into the database.

 Build API Endpoint:
  - Develop an API using a web framework of your choice (e.g., FastAPI, Django).
  - Implement a single API endpoint: /customers/:id/stats?from=YYYY-MM-DD
  - This endpoint should return daily statistics for a specific customer starting from the given date.
  - The statistics should include:
  - Total number successful and failed requests
  - Uptime
  - Average latency, median latency and p99 latency
