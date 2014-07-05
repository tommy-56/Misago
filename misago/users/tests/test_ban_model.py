#-*- coding: utf-8 -*-
from django.test import TestCase
from misago.users.models import Ban, BAN_USERNAME, BAN_EMAIL, BAN_IP


class BansManagerTests(TestCase):
    def setUp(self):
        Ban.objects.bulk_create([
            Ban(test=BAN_USERNAME, banned_value='bob'),
            Ban(test=BAN_EMAIL, banned_value='bob@test.com'),
            Ban(test=BAN_IP, banned_value='127.0.0.1'),
        ])

    def test_find_ban_for_banned_name(self):
        """find_ban finds ban for given username"""
        self.assertTrue(Ban.objects.find_ban(username='Bob') != None)
        with self.assertRaises(Ban.DoesNotExist):
            Ban.objects.find_ban(username='Jeb')

    def test_find_ban_for_banned_email(self):
        """find_ban finds ban for given email"""
        self.assertTrue(Ban.objects.find_ban(email='bob@test.com') != None)
        with self.assertRaises(Ban.DoesNotExist):
            Ban.objects.find_ban(email='jeb@test.com')

    def test_find_ban_for_banned_ip(self):
        """find_ban finds ban for given ip"""
        self.assertTrue(Ban.objects.find_ban(ip='127.0.0.1') != None)
        with self.assertRaises(Ban.DoesNotExist):
            Ban.objects.find_ban(ip='42.0.0.1')

    def test_find_ban_for_all_bans(self):
        """find_ban finds ban for given values"""
        valid_kwargs = {'username': 'bob', 'ip': '42.51.52.51'}
        self.assertTrue(Ban.objects.find_ban(**valid_kwargs) != None)

        invalid_kwargs = {'username': 'bsob', 'ip': '42.51.52.51'}
        with self.assertRaises(Ban.DoesNotExist):
            Ban.objects.find_ban(**invalid_kwargs)


class BanTests(TestCase):
    def test_test_value_literal(self):
        """ban correctly tests given values"""
        test_ban = Ban(banned_value='bob')

        self.assertTrue(test_ban.test_value('bob'))
        self.assertFalse(test_ban.test_value('bobby'))

    def test_test_value_starts_with(self):
        """ban correctly tests given values"""
        test_ban = Ban(banned_value='bob*')

        self.assertTrue(test_ban.test_value('bob'))
        self.assertTrue(test_ban.test_value('bobby'))

    def test_test_value_middle_match(self):
        """ban correctly tests given values"""
        test_ban = Ban(banned_value='b*b')

        self.assertTrue(test_ban.test_value('bob'))
        self.assertTrue(test_ban.test_value('bobby'))

    def test_test_value_middle_match(self):
        """ban correctly tests given values"""
        test_ban = Ban(banned_value='*bob')

        self.assertTrue(test_ban.test_value('lebob'))
        self.assertFalse(test_ban.test_value('bobby'))
