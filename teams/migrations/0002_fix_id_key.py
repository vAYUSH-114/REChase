from django.db import migrations

def drop_not_null_id_key(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'social_auth_usersocialauth' AND column_name = 'id_key';
        """)
        if cursor.fetchone():
            cursor.execute("ALTER TABLE social_auth_usersocialauth ALTER COLUMN id_key DROP NOT NULL;")

class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(drop_not_null_id_key, reverse_code=migrations.RunPython.noop),
    ]
