from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base providing self-updating ``created_at`` / ``updated_at``.

    Reused by domain models across modules to keep audit fields consistent.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
