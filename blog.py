#!/usr/bin/env python

# [START imports]
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)  # autoescape is important!
# [END imports]

BLOG_NAME = 'The Blog'
NUMBER_OF_POSTS = 10

# [START data structures]


class Author(ndb.Model):

    """Author model storing credentials"""
    identity = ndb.StringProperty()
    email = ndb.StringProperty()


class Post(ndb.Model):

    """Main model for blog posts"""
    author = ndb.StructuredProperty(Author)
    title = ndb.StringProperty(indexed=True)
    content = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)


class Comment(ndb.Model):

    """Additional model for all those comments"""
    author = ndb.StructuredProperty(Author)
    post = ndb.StructuredProperty(Post)
    text = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)


class Like(ndb.Model):
    author = ndb.StructuredProperty(Author)
    post = ndb.StructuredProperty(Post)
# [END data structures]


# [START views]
class MainPage(webapp2.RequestHandler):

    def get(self):
        posts = Post.query().order(-Post.date).fetch(NUMBER_OF_POSTS)

        # google strongly recommends the use of the user api
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_data = {
            'blog': BLOG_NAME,
            'posts': posts,
            'user': user,
            'url': url,
            'url_text': url_linktext
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_data))


class NewPost(webapp2.RequestHandler):

    def get(self):
        template_data = {
            'blog': BLOG_NAME,
            'user': users.get_current_user()
        }
        template = JINJA_ENVIRONMENT.get_template('new_post.html')
        self.response.write(template.render(template_data))

    def post(self):
        user = users.get_current_user
        if user:
            if len(self.request.get('content')) > 3 and len(self.request.get('title')) > 3:
                posting = Post(author=Author(
                    identity=users.get_current_user().user_id(),
                    email=users.get_current_user().email()),
                    content=self.request.get('content'),
                    title=self.request.get('title')
                )
                posting.put()
                self.redirect('/post/'+posting.key.urlsafe())


class ShowPost(webapp2.RequestHandler):

    def get(self, post_id):
        posting = ndb.Key(urlsafe=post_id).get()
        template_data = {
            'blog': BLOG_NAME,
            'user': users.get_current_user(),
            'post': posting,
            'comments': Comment.query(Comment.post == posting).order(Comment.date).fetch(10),
            'likes': Like.query(Like.post == posting).count()
        }
        template = JINJA_ENVIRONMENT.get_template('post.html')
        self.response.write(template.render(template_data))


class DeletePost(webapp2.RequestHandler):

    """Delete Posts if owned by user"""

    def get(self, post_id):
        post = ndb.Key(urlsafe=post_id).get()
        user = users.get_current_user()
        if post.author.identity == users.get_current_user().user_id():
            post.key.delete()
            self.redirect('/')
        else:
            self.response.set_status(403)


class EditPost(webapp2.RequestHandler):

    def get(self, post_id):
        post = ndb.Key(urlsafe=post_id).get()
        template_data = {
            'blog': BLOG_NAME,
            'user': users.get_current_user(),
            'post': post
        }
        template = JINJA_ENVIRONMENT.get_template('edit_post.html')
        self.response.write(template.render(template_data))

    def post(self, post_id):
        post = ndb.Key(urlsafe=post_id).get()
        user = users.get_current_user()
        if post.author.identity == users.get_current_user().user_id():
            post.title = self.request.get('title')
            post.content = self.request.get('content')
            post.put()
            self.redirect('/post/'+post.key.urlsafe())
        else:
            self.response.set_status(403)


class AddComment(webapp2.RequestHandler):

    def post(self, post_id):
        user = users.get_current_user()
        post = ndb.Key(urlsafe=post_id).get()
        if user:
            comment = Comment(author=Author(
                identity=users.get_current_user().user_id(),
                email=users.get_current_user().email()),
                post=post, text=self.request.get('text'))
            comment.put()
            self.redirect('/post/'+post.key.urlsafe())
        else:
            self.response.set_status(403)


class LikePost(webapp2.RequestHandler):

    def get(self, post_id):
        user = users.get_current_user()
        post = ndb.Key(urlsafe=post_id).get()
        # check if already liked
        like = Like.query(
            Like.author.identity == user.user_id(), Like.post == post).get()
        if like == None:
            like = Like(author=Author(
                identity=users.get_current_user().user_id(),
                email=users.get_current_user().email()),
                post=post)
            like.put()
        self.redirect('/post/'+post.key.urlsafe())
# [END views]

# [START url map]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/new_post', NewPost),
    ('/post/(\S+)', ShowPost),
    ('/delete/(\S+)', DeletePost),
    ('/edit/(\S+)', EditPost),
    ('/new_comment/(\S+)', AddComment),
    ('/like/(\S+)', LikePost),

], debug=True)
# [END url map]
