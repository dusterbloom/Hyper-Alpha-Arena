"""
Migration 004: Add Wallet Private Key Encrypted Field

Adds field to support KISS wallet integration (Phase 3):
- wallet_private_key_encrypted: Encrypted private key for automated trading

This migration is idempotent and backward compatible.
All new fields are optional (nullable).

Usage:
    cd backend
    uv run python database/migrations/004_add_wallet_private_key.py
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DB_PATH = Path(__file__).parent.parent.parent / "data.db"


def column_exists(cursor, table_name: str, column_name: str) -> bool:
    """Check if column exists in table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def add_wallet_private_key_field(cursor):
    """Add wallet_private_key_encrypted field to accounts table."""
    print("\n=== Adding Wallet Private Key Field ===")

    # Check and add wallet_private_key_encrypted
    if not column_exists(cursor, "accounts", "wallet_private_key_encrypted"):
        print("  Adding wallet_private_key_encrypted column...")
        cursor.execute("""
            ALTER TABLE accounts
            ADD COLUMN wallet_private_key_encrypted VARCHAR(500) NULL
        """)
        print("  ✓ wallet_private_key_encrypted added")
    else:
        print("  ℹ wallet_private_key_encrypted already exists")


def verify_migration(cursor):
    """Verify migration was successful."""
    print("\n=== Verifying Migration ===")

    # Check wallet_private_key_encrypted
    if column_exists(cursor, "accounts", "wallet_private_key_encrypted"):
        print("  ✓ wallet_private_key_encrypted column exists")
    else:
        print("  ✗ wallet_private_key_encrypted column missing!")
        return False

    # Check account count
    cursor.execute("SELECT COUNT(*) FROM accounts")
    account_count = cursor.fetchone()[0]
    print(f"  ✓ {account_count} accounts found")

    # Verify all accounts have NULL values for new field (expected)
    cursor.execute("""
        SELECT COUNT(*) FROM accounts
        WHERE wallet_private_key_encrypted IS NOT NULL
    """)
    non_null_count = cursor.fetchone()[0]
    print(f"  ℹ {non_null_count} accounts with encrypted private key configured")

    return True


def main():
    """Run migration."""
    print("\n" + "=" * 60)
    print("Migration 004: Add Wallet Private Key Encrypted Field")
    print("=" * 60)

    if not DB_PATH.exists():
        print(f"\n✗ Database not found at {DB_PATH}")
        print("  Create database first by running the application")
        sys.exit(1)

    print(f"\nDatabase: {DB_PATH}")

    # Backup recommendation
    print("\n⚠️  RECOMMENDED: Backup database before migration")
    print(f"  cp {DB_PATH} {DB_PATH}.backup")
    response = input("\nContinue with migration? (yes/no): ")

    if response.lower() not in ["yes", "y"]:
        print("Migration cancelled")
        sys.exit(0)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Add wallet private key field
        add_wallet_private_key_field(cursor)

        # Commit changes
        conn.commit()
        print("\n✓ Migration committed successfully")

        # Verify
        if verify_migration(cursor):
            print("\n✓ Migration verification passed")
            print("\n" + "=" * 60)
            print("✅ Migration 004 Complete!")
            print("=" * 60)
            print("\nNext Steps:")
            print("  1. Update account_routes.py to handle wallet credentials")
            print("  2. Add wallet input UI in SettingsDialog.tsx")
            print("  3. Test with Hyperliquid testnet wallet")
        else:
            print("\n✗ Migration verification failed")
            sys.exit(1)

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        print(f"  Restore from backup if needed:")
        print(f"  cp {DB_PATH}.backup {DB_PATH}")
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
