# -*- coding: utf-8 -*-

from django.conf import settings
from django.test import TestCase
from django.template import Context, Template

import os
import shutil

from admin_interface.models import Theme


class AdminInterfaceTestCase(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        pass

    def __render_template(self, string, context=None):

        context = context or {}
        context = Context(context)
        return Template(string).render(context)

    def __test_active_theme(self):

        theme = Theme.get_active_theme()
        print( theme )
        self.assertTrue(theme != None)
        self.assertTrue(theme.active)
        self.assertEqual(Theme.objects.filter( active = True ).count(), 1);

    def test_default_theme_created_if_no_themes(self):

        Theme.objects.all().delete()
        self.__test_active_theme()

    def test_default_theme_created_if_all_themes_deleted(self):

        Theme.objects.all().delete()
        self.__test_active_theme()

    def test_default_theme_activated_on_save_if_no_active_themes(self):

        Theme.objects.all().delete()
        theme = Theme.get_active_theme()
        theme.active = False
        theme.save()
        self.__test_active_theme()

    def test_default_theme_activated_after_update_if_no_active_themes(self):

        Theme.objects.all().delete()
        Theme.objects.all().update( active = False )
        self.__test_active_theme()

    def test_default_theme_activated_on_active_theme_deleted(self):

        Theme.objects.all().delete()
        theme_1 = Theme.objects.create( name = 'Custom 1', active = True )
        theme_2 = Theme.objects.create( name = 'Custom 2', active = True )
        theme_3 = Theme.objects.create( name = 'Custom 3', active = True )
        Theme.objects.filter( pk = Theme.get_active_theme().pk ).delete()
        self.assertEqual( Theme.get_active_theme().pk, 1 )

    def test_last_theme_activated_on_multiple_themes_created(self):

        Theme.objects.all().delete()
        theme_1 = Theme.objects.create( name = 'Custom 1', active = True )
        theme_2 = Theme.objects.create( name = 'Custom 2', active = True )
        theme_3 = Theme.objects.create( name = 'Custom 3', active = True )
        self.assertEqual( Theme.get_active_theme().pk, theme_3.pk )
        self.__test_active_theme()

    def test_templatetags(self):

        Theme.objects.all().delete()
        rendered = self.__render_template('{% load admin_interface_tags %}{% get_admin_interface_theme as theme %}{{ theme.name }}')
        self.assertEqual(rendered, 'TLM')

