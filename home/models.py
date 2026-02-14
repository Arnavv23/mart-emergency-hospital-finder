from django.db import models


class coordinates(models.Model):
    lat=models.IntegerField(max_length=200)
    lon=models.IntegerField(max_length=200)


# Create your models here.
