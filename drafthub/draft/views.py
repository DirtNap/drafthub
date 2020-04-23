from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Draft, Tag, Comment
from .forms import DraftForm


Blog = get_user_model()


class QueryFromBlog:
    def get_queryset(self):
        return Draft.objects.filter(
            blog__username=self.kwargs['username'])
 

class AccessRequired:
    def _user_has_access(self, request):
        if request.user.is_authenticated:
            self.object = self.get_object()
            return request.user == self.object.blog
        return redirect_to_login(request.get_full_path())

    def dispatch(self, request, *args, **kwargs):
        if not self._user_has_access(request):
            return redirect(self.object)
        return super().dispatch(request, *args, **kwargs)


class BlogListView(ListView):
    model = Draft
    template_name = 'draft/blog.html'
    context_object_name = 'blog_drafts'

    def get_queryset(self):
        self.blog = get_object_or_404(Blog, username=self.kwargs['username'])
        return self.model.objects.filter(blog=self.blog)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blog'] = self.blog
        context['github'] = self.blog.social_auth.get().extra_data

        return context


class DraftDetailView(QueryFromBlog, DetailView):
    model = Draft
    template_name = 'draft/draft.html'
    context_object_name = 'draft'

    def get_object(self):
        obj = super().get_object()

        obj.view_count += 1
        obj.save(update_fields=['view_count'])

        if self.request.user.is_authenticated:
            try:
                obj.last_update = self._get_draft_last_update(obj)
                obj.save(update_fields=['last_update'])
            except:
                pass

        return obj

    def _get_draft_last_update(self, obj):
        import requests
        import json
        from django.utils.dateparse import parse_datetime
        from .utils import get_data_from_url

        user = self.request.user
        social_user = self.request.user.social_auth.get()
        extra_data = social_user.extra_data
        token = extra_data['access_token']
        data = get_data_from_url(obj.github_url) 

        endpoint = 'https://api.github.com/graphql'
        query = f"""query {{
  viewer {{
    login
  }}
  rateLimit {{
    limit
    cost
    remaining
  }}
  repository(owner: "{data['login']}", name: "{data['repo']}"){{
    object(expression: "{data['branch']}"){{
      ... on Commit {{
        history(path: "{data['name']}", first:1){{
          edges {{
            node {{
              message
              oid
              author {{
                date
                user {{
                  name
                  url
                  login
                  isViewer
                }}
              }}
            }}
          }}
        }}
      }}
    }}
  }}
}}"""

        headers = {'Authorization': f'bearer {token}'}
        GraphiQL_connect = requests.post(
            endpoint,
            json={'query': query},
            headers=headers
        )
        api_data = json.loads(GraphiQL_connect.text)

        last_commit = api_data['data']['repository']['object']['history']
        last_commit = last_commit['edges'][0]['node']['author']['date']
        last_commit = parse_datetime(last_commit)
        pub_date = obj.pub_date
        last_update = obj.last_update

        tzinfo = last_commit.tzinfo
        last_commit = last_commit.replace(tzinfo=tzinfo).astimezone(tz=None)

        if last_commit > pub_date:
            return last_commit

        return None


class DraftCreateView(LoginRequiredMixin, CreateView):
    form_class = DraftForm
    template_name = 'draft/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request

        return kwargs

    def form_valid(self, form):
        form.instance.blog = self.request.user
        form.instance.slug = self._get_draft_unique_slug(form.instance)
        form.save()
        self._set_tags(form)

        return super().form_valid(form)

    def _get_draft_unique_slug(self, instance, unique_len=6):
        from django.utils.text import slugify
        from .utils import generate_random_string

        max_length = Draft._meta.get_field('slug').max_length
        author = instance.blog.username
        non_unique_slug = slugify(instance.title)
        non_unique_slug = non_unique_slug[: max_length - unique_len - 1]

        if non_unique_slug.endswith('-'):
            non_unique_slug = non_unique_slug[:-1]

        slug = non_unique_slug
        while Draft.objects.filter(slug=slug, blog__username=author):
            unique = generate_random_string()
            slug = non_unique_slug + '-' + unique

        return slug
    
    def _set_tags(self, form):
        from django.utils.text import slugify

        tag_str = form.cleaned_data['tags']
        draft = form.instance

        tag_names = tag_str.split(',')
        tag_names = [slugify(x) for x in tag_names[:5]]

        for tag_name in tag_names:
            tag_query = Tag.objects.filter(name__exact=tag_name)
            if tag_query.exists():
                tag = tag_query[0]
                draft.tags.add(tag)
            else:
                draft.tags.create(name=tag_name)


class DraftUpdateView(QueryFromBlog, AccessRequired, LoginRequiredMixin, UpdateView):
    form_class = DraftForm
    template_name = 'draft/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request

        return kwargs


class DraftDeleteView(QueryFromBlog, AccessRequired, LoginRequiredMixin, DeleteView):
    model = Draft
    template_name = 'draft/delete.html'
    context_object_name = 'draft'

    def get_success_url(self):
        args = (self.kwargs['username'],)
        return reverse_lazy('blog', args=args)


class LikeRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        slug = self.kwargs.get('slug')
        username = self.kwargs.get('username')
        obj = get_object_or_404(Draft, slug=slug, blog__username=username)

        user = self.request.user
        if user.is_authenticated:
            if user.likes.filter(slug=slug, blog__username=username).exists():
                obj.likes.remove(user)
            else:
                obj.likes.add(user)

        return obj.get_absolute_url()


class FavoriteRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        slug = self.kwargs.get('slug')
        username = self.kwargs.get('username')
        obj = get_object_or_404(Draft, slug=slug, blog__username=username)

        user = self.request.user
        if user.is_authenticated:
            if user.favorites.filter(slug=slug, blog__username=username).exists():
                obj.favorites.remove(user)
            else:
                obj.favorites.add(user)

        return obj.get_absolute_url()



from .utils import generate_random_string
class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['content']
    template_name = 'draft/form.html'

    def form_valid(self, form):
        form.instance.blog = self.request.user
        form.save()
        obj = get_object_or_404(
            Draft,
            slug=self.kwargs['slug'],
            blog__username=self.kwargs['username']
        )
        comment = form.instance
        obj.comments.add(comment)

        return super().form_valid(form)

    def get_success_url(self):
        args = (self.kwargs['username'], self.kwargs['slug'])
        return reverse_lazy('draft', args=args)


class CommentEditView(AccessRequired, LoginRequiredMixin, UpdateView):
    model = Comment
    template_name = 'draft/form.html'
    fields = ['content']


class CommentDeleteView(AccessRequired, LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'draft/delete.html'
    context_object_name = 'draft'

    def get_success_url(self):
        args = (self.kwargs['username'], self.kwargs['slug'])
        return reverse_lazy('draft', args=args)
