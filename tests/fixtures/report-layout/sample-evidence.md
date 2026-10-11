# Fictional CSV-export review evidence

Everything in this record is invented for a report-format demonstration. There is no actual PR, source implementation, benchmark, or application test run. Recorded results below are sample data, not executions during this work.

Intent: "Export all 2,400 matching rows in order for the agreed plain-row fixture."
Intent: "Keep peak export memory below 100 MB, including attachments."
Intent: "Only the requesting account can download its exports."
Intent: "Release resources when the client disconnects."
Intent is unspecified for detecting or retrying an incomplete download.

Fictional base: look up the export by export ID and account ID, fetch all rows, assemble the CSV, and then send headers and bytes. A lookup for another account returns 404. A row-fetch failure before response start returns 500 without CSV bytes.
Fictional head: look up the export by export ID only, send headers, then fetch and stream each batch. A later row-fetch failure terminates the stream after earlier chunks have been sent. Attachments still accumulate in memory. Cancellation cleanup has not been inspected.
Unchanged within this fictional model: row selection, row ordering, and CSV column names. No claim is made about other inputs or real callers.

Fictional row-count run at sample-head: 2,400 matching rows and 2,400 exported rows, in the expected order. One plain-row fixture; other inputs untested.
Fictional memory run at sample-head: 42 MB for plain rows and 146 MB with attachments, against the 100 MB target. Single fixture per case; no repeated measurements, distribution, or comparable base measurement is available.
Fictional account-isolation run: sample-base returned 404 for another account; sample-head returned 200 and CSV data. This is a new failure in the fictional comparison, not a real-system finding.
No cancellation test or real browser completion check is present in the fictional record.

Sequence actor: Browser requests the export and receives response bytes; its treatment of incomplete downloads is not inspected.
Sequence actor: Export handler resolves an export, sends headers, and coordinates row streaming; cleanup remains unknown.
Sequence actor: Store returns an export record or batches of rows, and can return a read error.
Sequence edge: Browser requests a download from Export handler.
Sequence edge: Export handler asks Store for the export by ID, without account filtering (changed).
Sequence edge: Store returns the export record to Export handler.
Sequence edge: Export handler sends HTTP 200 and headers to Browser before fetching all rows (changed).
Sequence edge: For each batch, Export handler asks Store for rows.
Sequence edge: On a successful read, Store returns rows to Export handler, which sends a CSV chunk to Browser.
Sequence edge: On a failed read, Store returns a read error to Export handler, which terminates the stream after earlier chunks. Browser interpretation remains unknown.

Illustrative head pseudocode, not executable source: resolve export by ID; send headers; for each fetched batch, send CSV rows. Account filtering present in the fictional base is missing at head. No inference about cleanup implementation is supported.
Consumers: the browser downloader and an automated importer receive the CSV. Neither consumer's completion detection or retry behavior has been inspected. Repeating an import might duplicate records; that is a question, not an established defect.
Deployment: the fictional interface keeps the same download route and CSV fields. Mixed-version rollout, rollback effects, logs, and metrics were not inspected; no operational assurance is given.

Illustrative lifecycle for a nonempty fictional export: headers are sent before streaming. The first row batch enters Streaming, later batches keep that state, and sending the last row enters All rows sent. A read failure during streaming enters Terminated with partial CSV. A client disconnect enters Disconnected; cleanup remains unknown. These are explanatory states, not inspected implementation enums. All rows sent describes server output only, not client confirmation.
