#-*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
##############################################################################

{
    'name': 'C2c Cron Audittrail',
    'version': '0.1',
    'category': 'Generic Modules/Others',
    'description': """
     Better cron management. 
     Allows fully threaded crons to run in parallel.
     Cron run at the given time. Overlapping job of the same cron are not possible 
     but the cron next run will be calculated and done even if a job run was not done because 
     his predessessor was still running. Different crons can run in parallel !!!
     This is a good as it is dangerous !!!
     Cron state, succes execution date, output are visible in admin.    
    """,
    'author': 'camptocamp',
    'website': 'http://www.camptocamp.com',
    'depends': ['base'],
    'init_xml': [],
    'update_xml': ['c2c_cron_audittrail_view.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: