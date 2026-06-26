from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True,
        db_index=True,
    )
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True,
    )

    class Meta:
        abstract = True
