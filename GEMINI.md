## Gemini Agent Protocol

This document outlines the best practices and conventions for Gemini agents working within this repository.

### Integrating with Beads and MCP Agent Mail

**Core Principle:** Use Beads for task management and Agent Mail for communication and coordination.

**Workflow:**

1.  **Select a Task:** Use `bd ready --json` to find an available task. Prioritize tasks based on their urgency and lack of blockers.
2.  **Reserve Files:** Before starting work, reserve the relevant file paths using `file_reservation_paths`.
    *   **`project_key`**: The absolute path to this repository.
    *   **`agent_name`**: Your registered agent name.
    *   **`paths`**: A list of file globs you intend to modify.
    *   **`ttl_seconds`**: A reasonable time-to-live for the reservation (e.g., 3600 for 1 hour).
    *   **`exclusive`**: `true` for write access.
    *   **`reason`**: The Beads issue ID (e.g., "bd-123").
3.  **Announce Your Work:** Send a message using `send_message`.
    *   **`thread_id`**: The Beads issue ID.
    *   **`subject`**: `[<issue-id>] Starting: <Task Title>`
    *   **`ack_required`**: `true`
4.  **Work and Communicate:**
    *   Keep all discussion related to the task within the same message thread.
    *   Reply to the thread with progress updates, questions, and attachments.
5.  **Complete the Task:**
    *   Close the issue in Beads: `bd close <issue-id> --reason "Completed"`
    *   Release your file reservations: `release_file_reservations`
    *   Send a final update to the message thread: `[<issue-id>] Completed` with a summary of your work.

**Identifier Mapping:**

*   **Mail `thread_id`**: The `bd-###` issue ID.
*   **Mail `subject`**: Start with `[bd-###]`.
*   **File Reservation `reason`**: The `bd-###` issue ID.
*   **Commit Messages**: Include `bd-###` for traceability.
