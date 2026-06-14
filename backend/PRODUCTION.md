# EduTrack Production Operations

## WSGI

Windows:

```powershell
python serve.py
```

Linux:

```bash
gunicorn --workers 4 --threads 2 --timeout 120 --bind 127.0.0.1:5000 wsgi:app
```

Place Nginx, IIS, Apache, or a managed HTTPS load balancer in front of the
application. Forward `X-Forwarded-Proto` and `X-Forwarded-For`.

## Required Environment

Production requires PostgreSQL and shared Redis. Startup fails when
`RATELIMIT_STORAGE_URI` uses `memory://` in production.

Set and protect:

- `SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL`
- `CORS_ORIGINS`, `FORCE_HTTPS=true`, `TRUST_PROXY=true`
- `RATELIMIT_STORAGE_URI=redis://...`
- `JWT_BLOCKLIST_STORAGE_URI=redis://...`
- `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE`
- `MAX_CONTENT_LENGTH`, `MATERIAL_UPLOAD_PATH`, `BACKUP_PATH`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`, `SMTP_USE_TLS`, `SMTP_USE_SSL`, `SMTP_TIMEOUT`

Configure the reverse-proxy request-body limit to the same byte limit as
`MAX_CONTENT_LENGTH`.

## PostgreSQL Network Access

Use a dedicated application user. Do not expose port 5432 publicly.

In `postgresql.conf`, bind only to loopback or a private interface:

```conf
listen_addresses = '127.0.0.1'
```

If the application and database are on separate private hosts, use the
database's private IP and allow only the application subnet in `pg_hba.conf`:

```conf
hostssl edutrack edutrack_app 10.20.0.0/24 scram-sha-256
```

Block public access with the host firewall or cloud security group.

## Backups

Run `scripts/backup_postgres.ps1` from Windows Task Scheduler or
`scripts/backup_postgres.sh` from cron. Test restoration regularly:

```bash
createdb edutrack_restore_test
pg_restore --dbname=edutrack_restore_test backup.dump
```

Store encrypted copies off-host. A backup that has never been restored is not
considered verified.

The bundled backup scripts include `MATERIAL_UPLOAD_PATH` when it exists.
EduTrack currently stores learning materials on the local filesystem, so use a
single application host or mount the same durable shared volume on every host.
For horizontally scaled deployments, migrate uploads to S3-compatible object
storage before adding hosts.

## Readiness and Monitoring

- Liveness: `GET /api/health`
- PostgreSQL readiness: `GET /api/ready`
- Prometheus metrics: `GET /api/metrics`

Send application logs to a centralized collector and alert on HTTP 5xx rate,
readiness failures, Redis failures, PostgreSQL connection saturation, and
backup job failures. Alert destinations are deployment-specific and are not
configured in this repository.

Restrict `/api/metrics` to the monitoring network at the reverse proxy.

## Load Tests

Install load-test dependencies:

```bash
pip install -r loadtests/requirements.txt
```

Run against staging, never production:

```bash
locust -f loadtests/locustfile.py --host=https://staging-api.example.com
```

Set `LOADTEST_EMAIL`, `LOADTEST_PASSWORD`, and `LOADTEST_ROLE`. Write testing
is disabled unless `ENABLE_WRITE_LOAD_TEST=true`.

For a 2,000-user validation, record p50/p95/p99 latency, error rate, active
PostgreSQL connections, Redis errors, and worker saturation. Keep:

`hosts * workers * (DB_POOL_SIZE + DB_MAX_OVERFLOW) < max_connections`

with capacity left for migrations, monitoring, and administrator sessions.
