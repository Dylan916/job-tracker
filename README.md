# job-tracker

A command-line tool for tracking job applications throughout your recruiting cycle. Log applications, update their status as you progress, get reminders for stale follow-ups, and view a summary of where you stand.

## Usage

### Install

```bash
uv add "git+https://github.com/Dylan916/job-tracker.git"
```

### Add an application

```bash
jobs add --company "Shopify" --role "Data Engineer Intern" --status applied
jobs add --company "SDSC" --role "Developer Intern" --location "Remote" --date 2026-06-01 --notes "Follow up Friday"
```

### List applications

```bash
jobs list
jobs list --status interviewing
jobs list --company "Shop"
```

Valid statuses: `applied`, `oa`, `phone`, `interviewing`, `offer`, `rejected`, `withdrawn`

### Update an application

```bash
jobs update 1 --status phone
jobs update 1 --notes "Recruiter: Jenny, follow up Friday"
```

### Delete an application

```bash
jobs delete 1
jobs delete 1 --yes
```

### View stats

```bash
jobs stats
```

### Get follow-up reminders

```bash
jobs remind
jobs remind --days 14
```