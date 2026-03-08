---
name: apple-events
description: Use this skill whenever the user wants to manage their Apple Reminders or Calendars using the `event` CLI tool. It provides instructions on how to create, view, update, and delete reminders, as well as interact with calendar events.
---

# Apple Reminders and Calendar CLI (`event`)

Use the `event` CLI to manage Apple Reminders and Calendars directly from the terminal. You can create, view, update, and delete reminders and subtasks, as well as view and create calendar events.

## Setup & Constraints

- **macOS-only**.
- Requires Apple Notes.app, Reminders.app, and Calendar.app to be accessible.
- If prompted, the user must grant Automation/Full Access permissions in System Settings > Privacy & Security > Reminders / Calendars.
- Some advanced reminder features (tags, flagged, parentTitle, url) require the `AdvancedReminderEdit` Shortcut to be installed (https://www.icloud.com/shortcuts/b578334075754da9ba6e50b501515808). If it's not installed, use the `--no-shortcuts` flag to disable these features and only use basic fields.

## General Usage

All commands support the `--json` flag to output results in JSON format, which is easier for you to parse.

## Reminders Management

### List Reminders
- List all incomplete reminders: `event reminders list`
- List including completed: `event reminders list --completed`
- Filter by specific list: `event reminders list --list "List Name"`

### Create Reminders
- Basic creation: `event reminders create --title "Buy groceries"`
- With details: `event reminders create --title "Project meeting" --list "Work" --due "2026-03-10 14:00:00" --priority 1 --notes "Discuss Q3 goals"`
- With advanced features (requires Shortcut): `event reminders create --title "Urgent bug" --tags "bug,urgent" --flagged true --url "https://github.com/issues/1"`

### Update Reminders
- Mark as completed: `event reminders update --id <UUID> --completed`
- Change title and priority: `event reminders update --id <UUID> --title "New Title" --priority 5`
- Add/remove flag (requires Shortcut): `event reminders update --id <UUID> --flagged true` or `--flagged false`

### Delete Reminders
- Delete by ID: `event reminders delete --id <UUID>`

### List Management
- List all reminder lists: `event reminders lists list`
- Create a new list: `event reminders lists create "New List Name"`
- Delete a list: `event reminders lists delete "List Name"`

### Subtasks
- List subtasks for a reminder: `event reminders subtasks list --id <UUID>`
- Create a subtask (requires Shortcut): `event reminders create --title "Subtask" --parent-title "Parent Task Title"`
- Create subtask directly (bypass Shortcut): `event reminders subtasks create --id <UUID> --title "Subtask Title"`
- Update subtask: `event reminders subtasks update --id <Parent-UUID> --subtask-id <Subtask-UUID> --completed`
- Delete subtask: `event reminders subtasks delete --id <Parent-UUID> --subtask-id <Subtask-UUID>`

## Calendar Management

### List Events
- List upcoming events (default 7 days): `event calendar list`
- List for specific date range: `event calendar list --start "2026-03-01" --end "2026-03-31"`
- Filter by specific calendar: `event calendar list --calendar "Work"`

### Limitations & Notes

- **Dates**: Must use `yyyy-MM-dd HH:mm:ss` format (e.g., "2026-03-10 14:00:00").
- **Priority**: 1 = High, 5 = Medium, 9 = Low. 0 = None.
- **Subtasks & Tags storage**: Due to EventKit limitations, `event` stores tags and subtasks inside the reminder's `notes` field separated by `---`. Be careful if manually editing notes.
