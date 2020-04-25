from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class Blog(AbstractUser):
    bio = models.TextField(max_length=160, default='get_from_github')
    favorited_drafts = models.ManyToManyField('draft.draft', blank=True, related_name='favorited_by')

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        args = (self.username,)
        return reverse('blog', args=args)


    class Meta(AbstractUser.Meta):
        verbose_name = 'Blog'
        verbose_name_plural = 'Blogs'

