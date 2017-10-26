# -*- coding: utf-8 -*-
'''
Created on Oct 25, 2017

@author: theo
'''
from acacia.meetnet.models import Network, Well, Datalogger, LoggerPos
from acacia.data.models import Project, aware, DataPoint
from django.contrib.gis.geos import Point
from acacia.data.util import RDNEW
from django.core.management.base import BaseCommand
import logging
import csv 
from acacia.meetnet.util import register_well, register_screen
from datetime import datetime
from django.conf import settings
from acacia.data.generators.dino import Dino
from django.contrib.auth.models import User
import pytz
logger = logging.getLogger(__name__)

def asfloat(x,scale = 1.0):
    try:
        return float(x) * scale
    except:
        return None

class Command(BaseCommand):
    help = 'Import zip file from Dinoloket'
    
    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str)

    def handle(self, *args, **options):
        files = options['files']
        net = Network.objects.first()
        prj = Project.objects.first()
        for fname in files:
            logger.info('Importing data from {}'.format(fname))
            dino = Dino()
            for pathname, data in dino.iter_zip(fname):
                if not data:
                    continue
                x = asfloat(data['X-coordinaat'])
                y = asfloat(data['Y-coordinaat'])
                name = data['Externe aanduiding']
                nitg = data['Locatie']
                maaiveld = asfloat(data['Maaiveld (cm t.o.v. NAP)'],0.01)
                try:
                    date = datetime.strptime(data['Startdatum'],'%d-%M-%Y')
                except:
                    date = None
                try:
                    loc = Point(x,y,srid=RDNEW)
                    well, created = Well.objects.update_or_create(name=name,defaults={
                           'network': net,
                           'nitg': nitg,
                           'location': loc,
                           'maaiveld': maaiveld,
                           'date': date
                           })
                    if created:
                        register_well(well)
                    bottom = asfloat(data['Onderkant filter (cm t.o.v. NAP)'],0.01)
                    top = asfloat(data['Bovenkant filter (cm t.o.v. NAP)'],0.01)
                    refpnt = asfloat(data['Meetpunt (cm t.o.v. NAP)'],0.01)
                    nr = data['Filternummer']
                    nr = int(nr) if nr else 1
                    screen, created = well.screen_set.update_or_create(nr=nr,defaults={'top': top, 'bottom': bottom, 'refpnt': refpnt})
                    if created:
                       register_screen(screen)
                       logger.info('Added {screen}'.format(screen=str(screen)))
                    else:
                       logger.info('Updated {screen}'.format(screen=str(screen)))
                    standen = data['standen']
                    if standen:
                        user = User.objects.get(username='theo')
                        tz = 'Europe/Amsterdam'
                        series, created = screen.mloc.series_set.get_or_create(name='Waterstand',defaults = {
                            'user': user,
                            'unit': 'm tov NAP',
                            'timezone': tz,
                            })
                        pts = []
                        tz = pytz.timezone(tz)
                        for s in standen:
                            date = s[2] + ' 12:00:00'
                            date = tz.localize(datetime.strptime(date,'%d-%m-%Y %H:%M:%S'))
                            value = asfloat(s[5], 0.01)
                            if value:
                                pts.append(DataPoint(series=series,date=date,value=value))
                        series.datapoints.all().delete()
                        series.datapoints.bulk_create(pts)
                        series.update_properties()
                except Exception as e:
                    logger.error('{}: {}'.format(name,e))
            
        logger.info('Import completed')
