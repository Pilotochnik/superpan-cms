# Generated manually for performance optimization

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_project_created_at'),
    ]

    operations = [
        # Индексы для Project
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_project_status ON projects_project (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_project_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_project_created_by ON projects_project (created_by_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_project_created_by;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_project_created_at ON projects_project (created_at);",
            reverse_sql="DROP INDEX IF EXISTS idx_project_created_at;"
        ),
        
        # Индексы для ProjectMember
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_project_member_project ON projects_projectmember (project_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_project_member_project;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_project_member_user ON projects_projectmember (user_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_project_member_user;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_project_member_role ON projects_projectmember (role);",
            reverse_sql="DROP INDEX IF EXISTS idx_project_member_role;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_project_member_active ON projects_projectmember (is_active);",
            reverse_sql="DROP INDEX IF EXISTS idx_project_member_active;"
        ),
    ]
