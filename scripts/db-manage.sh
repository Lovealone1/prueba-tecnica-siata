#!/usr/bin/env bash
set -e

# ==============================================================================
# Database Management Script (Alembic Wrapper)
# ==============================================================================
# Usage:
#   ./scripts/db-manage.sh up      -> Applies all pending migrations (To Head)
#   ./scripts/db-manage.sh down    -> Reverts all migrations (To Base)
#   ./scripts/db-manage.sh reset   -> Reverts all and applies all (Full Reset)
#   ./scripts/db-manage.sh status  -> Shows the current migration level
#   ./scripts/db-manage.sh history -> Shows the migration log
# ==============================================================================

# ROOT_DIR = root folder of the project
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMMAND=${1:-"help"}

case $COMMAND in
  up)
    echo ">> Upgrading database to head..."
    poetry run alembic upgrade head
    ;;
  down)
    echo ">> Downgrading database to base..."
    poetry run alembic downgrade base
    ;;
  reset)
    echo ">> Resetting database (Downgrade to base -> Upgrade to head)..."
    poetry run alembic downgrade base
    poetry run alembic upgrade head
    ;;
  status)
    echo ">> Current migration status:"
    poetry run alembic current
    ;;
  history)
    echo ">> Migration history:"
    poetry run alembic history
    ;;
  *)
    echo "Usage: $0 {up|down|reset|status|history}"
    echo "  up      : Upgrade to the latest migration (head)"
    echo "  down    : Downgrade all migrations (base)"
    echo "  reset   : Downgrade to base and then upgrade to head"
    echo "  status  : Show current migration level"
    echo "  history : Show migration history"
    exit 1
    ;;
esac
