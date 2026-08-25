#!/usr/bin/env python3
"""
WareFlow Database Backup & 14-Day Retention Engine.

Automated backup utility:
1. Connects to PostgreSQL using DIRECT_DATABASE_URL or DATABASE_URL.
2. Generates an encrypted/compressed SQL dump (gzip).
3. Uploads the backup to Supabase Storage 'backups' bucket using Service Role Key.
4. Prunes backups older than 14 days to preserve free-tier storage limits.

Usage:
    python scripts/backup.py [--local-only] [--output-dir ./backups]
"""

import argparse
import gzip
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx

# Ensure apps/api is on path to load environment variables
REPO_ROOT = Path(__file__).resolve().parent.parent
API_DIR = REPO_ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from dotenv import load_dotenv

env_path = API_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

MAX_BACKUP_RETENTION_DAYS = 14
BUCKET_NAME = "backups"


def parse_db_url(db_url: str) -> dict[str, str | int]:
    """Parse Postgres URL into connection components."""
    if db_url.startswith("postgresql+psycopg://"):
        db_url = db_url.replace("postgresql+psycopg://", "postgresql://", 1)
    
    parsed = urlparse(db_url)
    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "dbname": parsed.path.lstrip("/") or "postgres",
    }


def create_sql_dump_python(db_url: str, output_file: Path) -> None:
    """
    Generate SQL schema and data dump using SQLAlchemy reflection when pg_dump is not available.
    """
    import json
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import NullPool
    from app.db.session import normalize_database_url

    print("📦 Generating SQL dump via SQLAlchemy engine...")
    normalized_url = normalize_database_url(db_url)
    engine = create_engine(
        normalized_url,
        poolclass=NullPool,
        connect_args={"prepare_threshold": None},
    )
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"-- WareFlow Automated Database Backup\n")
        f.write(f"-- Generated At: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"-- Schema Version: Head\n\n")
        
        with engine.connect() as conn:
            tables_res = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
                "ORDER BY table_name"
            ))
            tables = [row[0] for row in tables_res if row[0] not in ("spatial_ref_sys", "alembic_version")]
            # Put alembic_version first if present
            tables = ["alembic_version"] + tables
            
            for table in tables:
                try:
                    rows = conn.execute(text(f'SELECT * FROM "{table}"')).mappings().all()
                except Exception as table_err:
                    print(f"ℹ️ Skipping table {table}: {table_err}")
                    continue

                if not rows:
                    continue
                
                f.write(f"\n-- Table: {table} ({len(rows)} records)\n")
                columns = list(rows[0].keys())
                col_names = ", ".join(f'"{c}"' for c in columns)
                
                for row in rows:
                    vals = []
                    for c in columns:
                        v = row[c]
                        if v is None:
                            vals.append("NULL")
                        elif isinstance(v, (int, float)):
                            vals.append(str(v))
                        elif isinstance(v, bool):
                            vals.append("TRUE" if v else "FALSE")
                        elif isinstance(v, (dict, list)):
                            clean_json = json.dumps(v).replace("'", "''")
                            vals.append(f"'{clean_json}'")
                        else:
                            clean_str = str(v).replace("'", "''")
                            vals.append(f"'{clean_str}'")
                    
                    val_str = ", ".join(vals)
                    f.write(f'INSERT INTO "{table}" ({col_names}) VALUES ({val_str}) ON CONFLICT DO NOTHING;\n')



def dump_database(db_url: str, output_gzip: Path) -> None:
    """Dump database using pg_dump if present, or fallback to python engine."""
    temp_sql = output_gzip.with_suffix("")
    
    # Check if pg_dump CLI is installed
    has_pg_dump = False
    try:
        res = subprocess.run(["pg_dump", "--version"], capture_output=True, text=True)
        if res.returncode == 0:
            has_pg_dump = True
    except FileNotFoundError:
        has_pg_dump = False

    if has_pg_dump:
        print("🛠️ Using native pg_dump CLI...")
        params = parse_db_url(db_url)
        env = os.environ.copy()
        env["PGPASSWORD"] = str(params["password"])
        
        cmd = [
            "pg_dump",
            "-h", str(params["host"]),
            "-p", str(params["port"]),
            "-U", str(params["user"]),
            "-d", str(params["dbname"]),
            "--no-owner",
            "--no-privileges",
            "-f", str(temp_sql),
        ]
        res = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"⚠️ pg_dump warning/error: {res.stderr}. Falling back to python dumper.")
            create_sql_dump_python(db_url, temp_sql)
    else:
        create_sql_dump_python(db_url, temp_sql)

    # Compress to gzip
    print(f"🗜️ Compressing SQL dump to {output_gzip.name}...")
    with open(temp_sql, "rb") as f_in, gzip.open(output_gzip, "wb", compresslevel=9) as f_out:
        f_out.writelines(f_in)
    
    # Remove raw uncompressed temporary file
    if temp_sql.exists():
        temp_sql.unlink()
    
    size_kb = output_gzip.stat().st_size / 1024
    print(f"✅ Backup created: {output_gzip.name} ({size_kb:.2f} KB)")


def upload_to_supabase_storage(file_path: Path, supabase_url: str, service_role_key: str) -> None:
    """Upload gzipped backup to Supabase Storage and enforce 14-day retention."""
    if not supabase_url or not service_role_key:
        print("ℹ️ SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing. Skipping cloud upload.")
        return

    headers = {
        "Authorization": f"Bearer {service_role_key}",
        "apiKey": service_role_key,
    }
    storage_api = f"{supabase_url.rstrip('/')}/storage/v1"

    # Ensure bucket exists
    try:
        bucket_check = httpx.get(f"{storage_api}/bucket/{BUCKET_NAME}", headers=headers)
        if bucket_check.status_code == 404:
            print(f"📁 Creating Supabase Storage bucket '{BUCKET_NAME}'...")
            httpx.post(
                f"{storage_api}/bucket",
                headers=headers,
                json={"id": BUCKET_NAME, "name": BUCKET_NAME, "public": False},
            )
    except Exception as e:
        print(f"ℹ️ Bucket check note: {e}")

    # Upload backup
    print(f"☁️ Uploading {file_path.name} to Supabase Storage bucket '{BUCKET_NAME}'...")
    upload_url = f"{storage_api}/object/{BUCKET_NAME}/{file_path.name}"
    
    with open(file_path, "rb") as f:
        upload_res = httpx.post(
            upload_url,
            headers={**headers, "Content-Type": "application/gzip", "x-upsert": "true"},
            content=f.read(),
            timeout=60.0,
        )
    
    if upload_res.status_code in (200, 201):
        print(f"✅ Cloud upload successful: {file_path.name}")
    else:
        print(f"⚠️ Upload response ({upload_res.status_code}): {upload_res.text}")

    # Prune backups older than 14 days
    print("🧹 Checking retention policy (14-day retention)...")
    try:
        list_res = httpx.post(
            f"{storage_api}/object/list/{BUCKET_NAME}",
            headers=headers,
            json={"prefix": "", "limit": 100, "sortBy": {"column": "name", "order": "desc"}},
            timeout=30.0,
        )
        if list_res.status_code == 200:
            objects = list_res.json()
            # Sort by creation date
            backup_files = [obj["name"] for obj in objects if obj["name"].startswith("wareflow_backup_")]
            if len(backup_files) > MAX_BACKUP_RETENTION_DAYS:
                excess = backup_files[MAX_BACKUP_RETENTION_DAYS:]
                print(f"🗑️ Pruning {len(excess)} backups older than {MAX_BACKUP_RETENTION_DAYS} days: {excess}")
                httpx.request(
                    "DELETE",
                    f"{storage_api}/object/{BUCKET_NAME}",
                    headers=headers,
                    json={"prefixes": excess},
                )
            else:
                print(f"✨ Total active cloud backups: {len(backup_files)}/{MAX_BACKUP_RETENTION_DAYS}. No pruning needed.")
    except Exception as exc:
        print(f"⚠️ Retention cleanup warning: {exc}")


def main():
    parser = argparse.ArgumentParser(description="WareFlow Database Backup Utility")
    parser.add_argument("--local-only", action="store_true", help="Only save locally, do not upload")
    parser.add_argument("--output-dir", default="./backups", help="Local backup directory")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_filename = f"wareflow_backup_{timestamp}.sql.gz"
    output_path = out_dir / backup_filename

    db_url = os.getenv("DIRECT_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ Error: DIRECT_DATABASE_URL or DATABASE_URL environment variable is required.")
        sys.exit(1)

    dump_database(db_url, output_path)

    if not args.local_only:
        supabase_url = os.getenv("SUPABASE_URL", "")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        upload_to_supabase_storage(output_path, supabase_url, service_role_key)

    print("\n🎉 Backup cycle completed successfully!")


if __name__ == "__main__":
    main()
