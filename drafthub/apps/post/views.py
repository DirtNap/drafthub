from django.shortcuts import redirect
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from drafthub.apps.post.models import Post
from drafthub.apps.core.utils import set_post_unique_slug


class PostView(DetailView):
    model = Post
    template_name = 'post/post.html'

    def get_queryset(self):
        return self.model.objects.filter(
            blog__author__username=self.kwargs['username'])


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    fields = ['raw_content_url', 'title']

    def form_valid(self, form):
        set_post_unique_slug(form.instance)
        return super().form_valid(form)

    def user_passes_test(self, request):
        if request.user.is_authenticated:
            self.object = self.get_object()
            return request.user == self.object.blog.author
        return redirect_to_login(request.get_full_path())

    def dispatch(self, request, *args, **kwargs):
        if not self.user_passes_test(request):
            return redirect(self.object)
        return super().dispatch(request, *args, **kwargs)
