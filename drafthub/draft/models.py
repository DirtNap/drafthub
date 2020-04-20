from django import forms
from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model


Blog = get_user_model()


class Draft(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    tags = models.ManyToManyField('draft.tag')
    comments = models.ManyToManyField('draft.comment', related_name='draft')
    likes = models.ManyToManyField(Blog, related_name='likes')
    favorites = models.ManyToManyField(Blog, related_name='favorites')

    github_url = models.URLField(max_length=1100)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    abstract = models.TextField(max_length=255, blank=True)
    pub_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(blank=True, null=True)
    view_count = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        kwargs = {
            'username': self.blog.username,
            'slug': self.slug,
        }
        return reverse('draft', kwargs=kwargs)

    class Meta:
        ordering = ['-pub_date',]
        verbose_name = 'draft'
        verbose_name_plural = 'drafties'


class Tag(models.Model):
    name = models.SlugField(max_length=25)

    def __str__(self):
        return self.name

class Comment(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    content = models.TextField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.blog.username + "'s comment (#{})".format(self.id)

    def get_absolute_url(self):
        kwargs = {
            'username': self.draft.get().blog.username,
            'slug': self.draft.get().slug,
        }
        return reverse('draft', kwargs=kwargs)

    class Meta:
        ordering = ['created',]
        verbose_name = 'comment'
        verbose_name_plural = 'comments'
