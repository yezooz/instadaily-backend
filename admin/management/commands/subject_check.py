# -*- coding: utf-8 -*-
import logging

from django.core.management.base import NoArgsCommand

import datetime


# from django.db import connection

from admin.models import Subject, SaveState


class Command(NoArgsCommand):
    def handle_noargs(self, **options):

        current_subject = Subject.objects.get_current()
        if current_subject is None:
            logging.error('Cannot find current subject!!!')
            return

        now = datetime.datetime.now()
        if now <= current_subject.active_to: return

        # invalidate currect subject
        current_subject.is_current = False

        # new subject to pick
        try:
            new_subject = Subject.objects.filter(
                active_from=datetime.datetime(now.year, now.month, now.day, 0, 0, 0)).get()
        except Subject.DoesNotExist:
            logging.error('Cannot find next subject!!!')
        new_subject.is_current = True

        s = SaveState.objects.get_by_k('recalc_subject_id')
        if s is not None and s.v != '0':
            logging.error('Cannot start recalculating new subject (%s), because old one (%s) is still active!!!' % (
            new_subject.id, current_subject.id))
            return

        # ready to go!
        current_subject.save()
        new_subject.save()

        s = SaveState.objects.get_by_k('recalc_subject_id')
        if s is None:
            s = SaveState()
            s.k = 'recalc_subject_id'
            s.v = str(current_subject.id)
            s.save()
        else:
            s.v = str(current_subject.id)
            s.save()

        s = SaveState.objects.get_by_k('recalc_action')
        if s is None:
            s = SaveState()
            s.k = 'recalc_action'
            s.v = 'points'
            s.save()
        else:
            s.v = 'points'
            s.save()
