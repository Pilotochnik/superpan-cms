# Generated manually for performance optimization

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0002_warehouseitem_equipment_photo_after_and_more'),
    ]

    operations = [
        # Индексы для WarehouseItem
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_warehouse_item_name ON warehouse_warehouseitem (name);",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_item_name;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_warehouse_item_type ON warehouse_warehouseitem (item_type);",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_item_type;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_warehouse_item_category ON warehouse_warehouseitem (category_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_item_category;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_warehouse_item_active ON warehouse_warehouseitem (is_active);",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_item_active;"
        ),
        
        # Индексы для WarehouseTransaction
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_warehouse_transaction_item ON warehouse_warehousetransaction (item_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_transaction_item;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_warehouse_transaction_type ON warehouse_warehousetransaction (transaction_type);",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_transaction_type;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_warehouse_transaction_date ON warehouse_warehousetransaction (created_at);",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_transaction_date;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_warehouse_transaction_user ON warehouse_warehousetransaction (created_by_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_transaction_user;"
        ),
    ]
