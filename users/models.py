from django.db import models

class UserProfile(models.Model):

    full_name = models.CharField(max_length=100)

    college = models.CharField(max_length=100)

    year = models.IntegerField()

    branch = models.CharField(max_length=100)

    def __str__(self):

        return self.full_name