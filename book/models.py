from django.db import models
from enum import Enum


class CoverType(Enum):
    HARD = "Hard"
    SOFT = "Soft"


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(
        choices=[(cover_type.name, cover_type.value) for cover_type in CoverType],
        max_length=4,
    )
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title
