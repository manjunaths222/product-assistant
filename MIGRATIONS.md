# Database Migrations Guide

## How Migrations Work in Deployed PostgreSQL

### Overview

This project uses **Alembic** for database schema migrations. Migrations allow you to:
- Track database schema changes over time
- Apply changes consistently across environments (dev, staging, production)
- Rollback changes if needed
- Collaborate on schema changes with version control

### Migration Workflow

#### 1. **Local Development**

When you make changes to database models (`app/models/db_models.py`):

```bash
# 1. Create a new migration
alembic revision --autogenerate -m "add_feasibility_table"

# 2. Review the generated migration file in alembic/versions/
#    - Check that it correctly reflects your model changes
#    - Adjust if needed (e.g., data migrations, custom SQL)

# 3. Test the migration locally
alembic upgrade head

# 4. Verify your changes work
#    - Run your application
#    - Test the new functionality

# 5. Commit and push
git add alembic/versions/XXXX_add_feasibility_table.py
git commit -m "Add feasibility table migration"
git push
```

#### 2. **Deployment (Render.com)**

When you push to GitHub, Render automatically:

1. **Builds** your Docker image
2. **Starts** the container
3. **Runs** `docker-entrypoint.sh` which executes:
   ```bash
   alembic upgrade head
   ```
4. **Applies** any pending migrations to the PostgreSQL database
5. **Starts** your FastAPI application

#### 3. **What Happens During Migration**

When `alembic upgrade head` runs:

1. **Connects** to PostgreSQL using `DATABASE_URL` environment variable
2. **Checks** the `alembic_version` table for current migration version
3. **Compares** with migration files in `alembic/versions/`
4. **Applies** any migrations that haven't been run yet
5. **Updates** `alembic_version` table with new version

### Migration Files Structure

```
alembic/
├── env.py              # Alembic configuration (connects to your models)
├── script.py.mako      # Migration template
├── versions/           # Migration files (one per schema change)
│   ├── 9994d71d1392_add_feasibility_table.py
│   └── ...
└── README
```

### Key Concepts

#### Migration Version Tracking

Alembic creates an `alembic_version` table in your database:

```sql
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
```

This table stores the current migration version (e.g., `9994d71d1392`).

#### Idempotent Migrations

- Running `alembic upgrade head` multiple times is **safe**
- Alembic only applies migrations that haven't been run
- Already-applied migrations are skipped automatically

#### Migration Dependencies

Each migration file has:
- `revision`: Unique identifier (e.g., `9994d71d1392`)
- `down_revision`: Previous migration (creates a chain)
- `upgrade()`: Function that applies the migration
- `downgrade()`: Function that rolls back the migration

### Common Commands

#### Check Current Migration Status

```bash
# Show current database version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

#### Apply Migrations

```bash
# Apply all pending migrations (used in deployment)
alembic upgrade head

# Apply one migration at a time
alembic upgrade +1

# Apply up to specific revision
alembic upgrade <revision_id>
```

#### Rollback Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all migrations (⚠️ dangerous)
alembic downgrade base
```

#### Create New Migrations

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "description"

# Create empty migration (for custom SQL)
alembic revision -m "description"
```

### Deployment-Specific Details

#### Environment Variables

The `DATABASE_URL` environment variable is automatically used by Alembic:

```bash
# In Render.com, this is set automatically from your PostgreSQL service
DATABASE_URL=postgresql://user:password@host:port/database
```

#### First Deployment

On the first deployment:
1. Alembic creates the `alembic_version` table
2. Applies all migrations in order
3. Creates all database tables

If migrations fail, `init_db.py` runs as a fallback to create tables using `Base.metadata.create_all()`.

#### Subsequent Deployments

On each deployment:
1. Alembic checks current version
2. Applies only new migrations
3. Updates `alembic_version` table

### Troubleshooting

#### Migration Fails on Deployment

**Check logs in Render Dashboard:**
```bash
# Look for errors like:
# - "relation already exists" (migration already applied)
# - "column does not exist" (migration out of order)
# - "connection refused" (database connection issue)
```

**Solutions:**
1. Verify `DATABASE_URL` is correct
2. Check migration files are in the repository
3. Ensure database is accessible
4. Review migration file for errors

#### Database Out of Sync

If your database schema doesn't match your models:

```bash
# 1. Check current migration version
alembic current

# 2. Check what migrations exist
alembic history

# 3. Apply missing migrations
alembic upgrade head
```

#### Need to Reset Database (⚠️ Data Loss)

**Only for development/testing:**

```bash
# 1. Drop all tables (⚠️ deletes all data)
#    Connect to database and run:
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

# 2. Re-run all migrations
alembic upgrade head
```

### Best Practices

1. **Always test migrations locally** before pushing
2. **Review auto-generated migrations** - Alembic can miss some changes
3. **Use descriptive migration messages** - helps track changes
4. **One migration per feature** - easier to review and rollback
5. **Backup database** before major schema changes
6. **Never edit applied migrations** - create new ones instead
7. **Keep migrations small** - large migrations are harder to debug

### Example: Adding the Feasibility Table

Here's what happened when we added the feasibility table:

1. **Model Change**: Added `Feasibility` class to `db_models.py`
2. **Created Migration**: 
   ```bash
   alembic revision --autogenerate -m "add_feasibility_table"
   ```
3. **Generated File**: `alembic/versions/9994d71d1392_add_feasibility_table.py`
4. **On Deployment**: 
   - Render runs `alembic upgrade head`
   - Migration creates `feasibilities` table
   - Updates `alembic_version` to `9994d71d1392`

### Monitoring Migrations

To verify migrations ran successfully:

1. **Check Render Logs**: Look for "Running database migrations..." message
2. **Query Database**: 
   ```sql
   SELECT * FROM alembic_version;
   ```
3. **Check Tables**: 
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public';
   ```

### Summary

- ✅ Migrations run **automatically** on every deployment
- ✅ Only **new migrations** are applied (idempotent)
- ✅ Migration history is **tracked** in `alembic_version` table
- ✅ Safe to run multiple times
- ✅ Can rollback if needed

The deployment process handles migrations automatically - you just need to commit and push your migration files!

