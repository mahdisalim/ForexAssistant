# Generated migration for adding tradingview_symbol field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='currencypair',
            name='tradingview_symbol',
            field=models.CharField(blank=True, help_text='TradingView symbol format (e.g., FX:EURUSD, TVC:GOLD)', max_length=50, null=True),
        ),
    ]
