# Generated manually for performance optimization

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0001_initial'),
    ]

    operations = [
        # Индексы для WarehouseItem
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_warehouse_item_type ON warehouse_warehouseitem (item_type);",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_item_type;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_warehouse_item_quantity ON warehouse_warehouseitem (current_quantity);",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_item_quantity;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_warehouse_item_min_quantity ON warehouse_warehouseitem (min_quantity);",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_item_min_quantity;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_warehouse_item_low_stock ON warehouse_warehouseitem (current_quantity, min_quantity) WHERE current_quantity <= min_quantity;",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_item_low_stock;"
        ),
        
        # Индексы для WarehouseTransaction
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_warehouse_transaction_item ON warehouse_warehousetransaction (item_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_transaction_item;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_warehouse_transaction_user ON warehouse_warehousetransaction (user_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_transaction_user;"
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
            "CREATE INDEX IF NOT EXISTS idx_warehouse_transaction_compound ON warehouse_warehousetransaction (item_id, transaction_type, created_at);",
            reverse_sql="DROP INDEX IF EXISTS idx_warehouse_transaction_compound;"
        ),
    ]