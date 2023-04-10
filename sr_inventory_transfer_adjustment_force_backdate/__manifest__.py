# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

{
    'name': 'Stock Transfer And Inventory Adjustment Force Back Date',
    'version': '15.0.0.3',
    'category': 'Inventory',
    "license": "OPL-1",
    'summary': 'odoo apps for transfer stock in back date adjust inventory in back date back date operation in stock stock operation in back date',
    'description': """
        stock back date movement
        back date stock transfer
        back date inventory adjustment
        back date stock operation
        inventory operations in back date
        delivery order in back date
        incoming shipment in back date
        process stock picking in back date
        make delivery order for previous old date
        make incoming shipment for previous old date
        adjust inventory in back date
        back dated inventory operation
        stock movement back dated
        increase inventory in previous date
        decrease inventory in previous date
        sitaram solutions odoo stock transfer back date
        sitaram solutions odoo inventory adjustment back date
        move your stock in previous date
        adjust your stock in previous date
""",
    "price": 10,
    "currency": 'EUR',
    'author': 'Sitaram',
    'depends': ['base','stock','stock_account'],
    'data': [
             'views/sr_inherit_stock_picking.xml',
             'views/sr_inherit_inventory_adjustment.xml'
    ],
    'website':'https://sitaramsolutions.in',
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://youtu.be/DSm732Kf6p4',
    "images":['static/description/banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
