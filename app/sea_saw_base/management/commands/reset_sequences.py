"""
Management command to reset PostgreSQL sequences for all tables.

Usage:
    python manage.py reset_sequences
    python manage.py reset_sequences --table sea_saw_attachment_attachment
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Reset PostgreSQL sequences to max(id) for all tables (or a specific table)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--table",
            type=str,
            help="Only reset the sequence for this specific table name",
        )

    def handle(self, *args, **options):
        specific_table = options.get("table")

        with connection.cursor() as cursor:
            if specific_table:
                tables = [specific_table]
            else:
                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    """
                )
                tables = [row[0] for row in cursor.fetchall()]

            reset_count = 0
            for table in tables:
                cursor.execute(
                    "SELECT pg_get_serial_sequence(%s, 'id')", [table]
                )
                row = cursor.fetchone()
                if not row or not row[0]:
                    continue

                seq_name = row[0]
                cursor.execute(
                    f"""
                    SELECT setval(
                        %s,
                        COALESCE((SELECT MAX(id) FROM "{table}"), 1)
                    )
                    """,
                    [seq_name],
                )
                new_val = cursor.fetchone()[0]
                self.stdout.write(f"  {table}: sequence reset to {new_val}")
                reset_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Done. Reset {reset_count} sequence(s).")
        )
