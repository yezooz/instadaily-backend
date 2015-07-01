# -*- coding: utf-8 -*-
import logging

from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings

import datetime


# from django.db import connection
from urllib2 import Request, urlopen, URLError, HTTPError
import simplejson as json

from admin import R
from admin.models import User, Photo, Subject


class Command(NoArgsCommand):
    def handle_noargs(self, **options):

        t = datetime.datetime.now() - datetime.timedelta(hours=4)

        s = Subject.objects.get_current()

        if s == None: return

        redis = R()

        for img in Photo.objects.filter(subject=s, is_blocked=False, date_updated__lt=t)[:20]:
            # print 'added %s' % img.instagram_id
            redis.add_photo(img.instagram_id)

        for img_id in redis.get_photos(50):
            # print 'processed %s' % img_id
            if (self.handle_img(img_id)) != True:
                redis.add_photo(img_id)

    def handle_img(self, img_id):

        img = Photo.objects.get_by_instagram_id(img_id)

        u = User.objects.get_by_name(img.user)
        if u.access_token == None or u.access_token == '':
            token = User.objects.get_by_name('yezooz').access_token
        else:
            token = u.access_token

        url = 'https://api.instagram.com/v1/media/%s?access_token=%s' % (img_id, token)

        req = Request(url)
        # req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)')
        try:
            response = urlopen(req)
        except HTTPError, e:
            if str(e) == 'HTTP Error 400: BAD REQUEST':
                img.points = 0
                img.total_score = 0
                img.is_blocked = True
                img.save()
                return True

            print url
            print str(e)
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code
            return False
        except URLError, e:
            print url
            print str(e)
            print 'We failed to reach a server.'
            # 	# print 'Reason: ', e.reason
            return False

        # everything is fine
        try:
            data = json.loads(response.read())
        except Exception, e:
            return False

        if not data.has_key('data'):
            if data.has_key('meta') and data['meta'].get('error_message') == 'invalid media id':
                img.points = 0
                img.total_score = 0
                img.is_blocked = True
                img.save()

                logging.info('Photo %s has been deleted' % img_id)
                return True

            if data.has_key('meta') and data['meta'].get('error_type') == 'APINotAllowedError':
                # just update
                img.save()

                logging.warning('APINotAllowedError - %s' % url)
                return True

            logging.warning('No data in fetched url: %s' % url)
            print 'No data in fetched url: %s' % url
            return False

        try:
            if img is None: return
            img.likes = data['data']['likes']['count']
            img.tags = data['data']['tags']
            img.save()

            return True

        except AttributeError:
            logging.warning('got no data? %s' % str(data))
            return False
