# -*- coding: utf-8 -*-
import logging
# import os, re, urllib
from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings

# from django.db import connection
from urllib2 import Request, urlopen, URLError, HTTPError
import simplejson as json

from admin.models import Tag, User, Photo, Subject


class Command(NoArgsCommand):
    def handle_noargs(self, **options):

        self.handle_tag('instadaily__')

    def handle_tag(self, tag_name):

        try:
            tag = Tag.objects.filter(name=tag_name).get()
        except Tag.DoesNotExist:
            tag = Tag()
            tag.name = tag_name
            tag.min_tag_id = 203525040
            tag.save()

        tag_name = tag_name.replace('__', '')

        url = 'https://api.instagram.com/v1/tags/%s/media/recent?access_token=627640.f59def8.9b0aa5e5317847579720140967ef1aa7&max_tag_id=%d' % (
        tag_name, tag.min_tag_id)

        req = Request(url)
        # req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)')
        try:
            response = urlopen(req)
        except HTTPError, e:
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code
            return
        except URLError, e:
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
            return

        # everything is fine
        data = json.loads(response.read())

        try:
            tag.min_tag_id = int(data['pagination']['next_max_tag_id'])
            tag.save()
        except KeyError:
            pass

        if not data.has_key('data'):
            logging.warning('No data in fetched url: %s' % url)
            return

        logging.info('Downloaded %d photos for tag #%s' % (len(data['data']), tag_name))
        for d in data['data']:
            Photo().add_or_update(d)

            u = User.objects.get_by_name(d['user']['username'])
            if u is None:
                u = User()
                u.instagram_id = d['user']['id']
                u.name = d['user']['username']
                u.pic = d['user']['profile_picture']
                # u.full_name = d['user']['full_name']
                u.points = 0
                u.vote_like = 0
                u.vote_dislike = 0
                try:
                    u.last_subject_id = Subject.objects.get_current().id
                except AttributeError:
                    logging.error('cannot find current subject!!!')
                    u.last_subject_id = 0
                u.last_subject_points = 0
                u.save()
