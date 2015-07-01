# -*- coding: utf-8 -*-
import logging
# from django.core.urlresolvers import reverse
from annoying.decorators import render_to
from admin.models import User, Subject
# from google.appengine.api import urlfetch
import simplejson as json

SECRET = ''


@render_to('auth.html')
def index(request):
    if request.method == 'POST' and request.POST.has_key('user'):

        u = json.loads(request.POST['user'])

        try:
            user = User.objects.filter(instagram_id=u['instagram_id']).get()
            user.token = u['token']
            user.access_token = u['access_token']  # instagram's one
            user.pic = u['pic']
            user.full_name = u['full_name']
            user.save()

        except User.DoesNotExist:
            user = User()
            user.token = u['token']
            user.access_token = u['access_token']
            user.name = u['name']
            user.instagram_id = u['instagram_id']
            user.full_name = u['full_name']
            user.pic = u['pic']
            user.photos = 0
            user.vote_like = u['vote_like']
            user.vote_dislike = u['vote_dislike']
            try:
                user.last_subject_id = Subject.objects.get_current().id
            except AttributeError:
                logging.error('cannot find current subject!!!')
                user.last_subject_id = 0
            user.last_subject_points = 0
            user.save()

    return {'body': ''}
