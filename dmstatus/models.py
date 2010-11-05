# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is django moz status.
#
# The Initial Developer of the Original Code is
# Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2010
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

'''
'''

from django.db import models

class JSONField(models.TextField):
    pass

class Master(models.Model):
    url = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'masters'


class Slave(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    masters = models.ManyToManyField(Master, through="Slaves_Masters",
                                     related_name='slaves')

    class Meta:
        db_table = 'slaves'

class Slaves_Masters(models.Model):
    "through-model for relation of slaves and masters"
    slave = models.ForeignKey(Slave, related_name='connecting_masters')
    master = models.ForeignKey(Master, related_name='connecting_slaves')
    connected = models.DateTimeField()
    disconnected = models.DateTimeField()

    class Meta:
        db_table = 'master_slaves'


class Patch(models.Model):
    patch = models.TextField()
    patchlevel = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = 'patches'


class Property(models.Model):
    name = models.CharField(max_length=40, null=True, blank=True)
    source = models.CharField(max_length=40, null=True, blank=True)
    value = JSONField()

    class Meta:
        db_table = 'properties'


class File(models.Model):
    path = models.CharField(max_length=400)

    class Meta:
        db_table = 'files'


class Change(models.Model):
    number = models.IntegerField()
    branch = models.CharField(max_length=50)
    files = models.ManyToManyField(File, through='File_Changes',
                                   related_name='changes')
    revision = models.CharField(max_length=50)
    who =  models.CharField(max_length=200)
    comments = models.TextField()
    when = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'changes'

class File_Changes(models.Model):
    file = models.ForeignKey(File)
    change = models.ForeignKey(Change)

    class Meta:
        db_table = 'file_changes'


class Sourcestamp(models.Model):
    branch = models.CharField(max_length=50)
    revision = models.CharField(max_length=50)
    patch = models.ForeignKey(Patch)
    changes = models.ManyToManyField(Change, through='Source_Changes',
                                     related_name='sources')

    class Meta:
        db_table = 'sourcestamps'

class Source_Changes(models.Model):
    source = models.ForeignKey(Sourcestamp, related_name='ordered_change')
    change = models.ForeignKey(Change, related_name='ordered_source')
    order = models.IntegerField()

    class Meta:
        db_table='source_changes'
        ordering = ['order']

class Builder(models.Model):
    name = models.CharField(max_length=200, unique=True)
    master = models.ForeignKey(Master)
    category = models.CharField(max_length=30)
    slaves = models.ManyToManyField(Slave, through='Builder_Slaves',
                                    related_name='builders')
    def __unicode__(self):
        return "%s (%s)" % (self.name, self.master.name)

    class Meta:
        db_table = 'builders'

class Builder_Slaves(models.Model):
    builder = models.ForeignKey(Builder, related_name='bslaves')
    slave = models.ForeignKey(Slave, related_name='sbuilders')
    added = models.DateTimeField()
    removed = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'builder_slaves'


class Request(models.Model):
    """XXX: No data for this model in the DB?"""
    submittime = models.DateTimeField(null=True, blank=True)
    builder = models.ForeignKey(Builder, related_name='requests')
    startcount = models.IntegerField()
    source = models.ForeignKey(Sourcestamp, related_name='requests',
                               null=True, blank=True)
    lost = models.IntegerField()
    cancelled = models.IntegerField()
    properties = models.ManyToManyField(Property,through='Request_Properties',
                                        related_name='requests')

    class Meta:
        db_table = 'requests'

class Request_Properties(models.Model):
    property = models.ForeignKey(Property)
    request = models.ForeignKey(Request)
    class Meta:
        db_table = 'request_properties'


class Build(models.Model):
    buildnumber = models.IntegerField()
    builder = models.ForeignKey(Builder, related_name='builds')
    slave = models.ForeignKey(Slave, related_name='builds')
    master = models.ForeignKey(Master, related_name='builds')
    starttime = models.DateTimeField(null=True, blank=True)
    endtime = models.DateTimeField(null=True, blank=True)
    result = models.IntegerField()
    reason = models.CharField(max_length=500, null=True, blank=True)
    source = models.ForeignKey(Sourcestamp, related_name='builds')
    properties = models.ManyToManyField(Property, through='Build_Properties',
                                        related_name='builds')
    requests = models.ManyToManyField(Request, through='Build_Requests',
                                      related_name='builds')
    lost = models.IntegerField()

    class Meta:
        db_table = 'builds'

class Build_Properties(models.Model):
    property = models.ForeignKey(Property)
    build = models.ForeignKey(Build)

    class Meta:
        db_table = 'build_properties'

class Build_Requests(models.Model):
    build = models.ForeignKey(Build)
    request = models.ForeignKey(Request)
    class Meta:
        db_table = 'build_requests'


class Step(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField()
    build = models.ForeignKey(Build, related_name='steps')
    order = models.IntegerField()
    starttime = models.DateTimeField(null=True, blank=True)
    endtime = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField()

    class Meta:
        db_table = 'steps'
