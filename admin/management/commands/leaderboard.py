# -*- coding: utf-8 -*-
import logging

from django.core.management.base import NoArgsCommand, CommandError

# from django.conf import settings

# from django.db import connection
# from urllib2 import Request, urlopen, URLError, HTTPError
# import simplejson as json

from admin import R
from admin.models import Photo, User, UserSubject, SaveState, Subject


class Leaderboard(object):
    def __init__(self, subject_id):
        self.subject_id = int(subject_id)
        self.current_subject = Subject.objects.get_current()

        self.redis = R()

    def points(self):
        subject = Subject.objects.get_by_id(self.subject_id)

        if self.redis.r.llen('photo:queue') > 50:
            print 'wait, still %d to process' % self.redis.r.llen('photo:queue')
            return

        i = 0
        for p in Photo.objects.filter(subject=subject, is_active=True, is_user_active=True, is_blocked=False,
                                      is_final_score=False, date_updated__lte=subject.active_to):
            self.redis.add_photo(p.instagram_id)
            i += 1

        if i == 0:
            s = SaveState.objects.get_by_k('recalc_action')
            s.v = 'final_score'
            s.save()

            print 'points. done.'

    def final_score(self):
        for p in Photo.objects.filter(subject__id=self.subject_id, is_active=True, is_user_active=True,
                                      is_blocked=False, is_final_score=False):
            # p.total_score = (p.likes + p.points) - p.dislikes
            p.total_score = (p.likes + p.points)
            p.is_final_score = True
            p.save()

        c = Photo.objects.filter(subject__id=self.subject_id, is_active=True, is_user_active=True, is_blocked=False,
                                 is_final_score=False).count()
        if c == 0:
            s = SaveState.objects.get_by_k('recalc_action')
            s.v = 'subject'
            s.save()

            print 'final score. done.'
        else:
            logging.info('still got %d+ in final_score' % c)

    def subject(self):
        for user in User.objects.filter(last_subject_id=self.subject_id).order_by('-points'):
            # top photo
            photo = Photo.objects.filter(user=user.name, subject__id=self.subject_id, is_active=True,
                                         is_user_active=True, is_blocked=False).order_by('-total_score')

            if photo.count() == 0:
                user.last_subject_id = self.current_subject.id
                user.save()
                continue

            photo = photo[0]

            us = UserSubject()
            us.subject_id = self.subject_id
            us.best_photo_id = photo.id
            us.user = user.name
            us.points = photo.total_score
            us.save()

            user.points += photo.total_score
            user.last_subject_id = self.current_subject.id
            user.last_subject_points = us.points
            user.save()

        c = User.objects.filter(last_subject_id=self.subject_id).count()
        if c == 0:
            s = SaveState.objects.get_by_k('recalc_action')
            s.v = 'leaderboard'
            s.save()

            print 'subject. done.'
        else:
            logging.info('still got %d+ in subject' % c)

    def leaderboard(self):

        subject = Subject.objects.get_by_id(self.subject_id)

        last_processed_id = self.redis.r.get('last_user_processed') or 0

        for user in User.objects.filter(id__gt=last_processed_id).order_by('id'):
            self.redis.r.zincrby('leaderboard', user.name, user.last_subject_points)

            self.redis.r.zincrby('leaderboard:year:%d' % subject.active_to.year, user.name, user.last_subject_points)

            self.redis.r.zincrby('leaderboard:year:%d:month:%d' % (subject.active_to.year, subject.active_to.month),
                                 user.name, user.last_subject_points)

            self.redis.r.zincrby('leaderboard:subject:%d' % self.subject_id, user.name, user.last_subject_points)

            self.redis.r.set('last_user_processed', user.id)

        s = SaveState.objects.get_by_k('recalc_action')
        s.v = ''
        s.save()

        s = SaveState.objects.get_by_k('recalc_subject_id')
        s.v = '0'
        s.save()

        self.redis.r.set('last_user_processed', 0)


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        s = SaveState.objects.get_by_k('recalc_action')
        ss = SaveState.objects.get_by_k('recalc_subject_id')

        if s is None or s.v == '' or ss is None or ss.v == '':
            return

        l = Leaderboard(ss.v)

        if s.v == 'points':
            l.points()
        elif s.v == 'final_score':
            l.final_score()
        elif s.v == 'subject':
            l.subject()
        elif s.v == 'leaderboard':
            l.leaderboard()
