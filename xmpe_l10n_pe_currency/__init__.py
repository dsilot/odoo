# -*- coding: utf-8 -*-

from . import models
from . import wizard

from odoo import api, SUPERUSER_ID


# TODO: Change settings values
def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    default = None
    currency_obj = env['res.currency'].sudo()
    codes = ['USD', 'EUR', 'CAD', 'GBP', 'CHF', 'JPY', 'CNY']
    currency_ids = currency_obj.search([('name', 'in', codes), '|', ('active', '=', True), ('active', '=', False)])
    for obj in currency_ids:
        original1 = {
            'name': obj.name + '-Venta',
            'currency_unit_label': obj.currency_unit_label + ' (Venta)',
            'rate_type': 'venta',
            'rate_inv': obj.rate,
            'symbol': obj.symbol,
            'rounding': obj.rounding,
            'decimal_places': obj.decimal_places,
            'currency_subunit_label': obj.currency_subunit_label,
            'position': obj.position,
            'active': True if obj.name == 'USD' else False
        }
        original2 = {
            'name': obj.name + '-Compra',
            'currency_unit_label': obj.currency_unit_label + ' (Compra)',
            'rate_type': 'compra',
            'rate_inv': obj.rate,
            'symbol': obj.symbol,
            'rounding': obj.rounding,
            'decimal_places': obj.decimal_places,
            'currency_subunit_label': obj.currency_subunit_label,
            'position': obj.position,
            'active': True if obj.name == 'USD' else False
        }
        obj.active = False
        currency_obj.create(original1)
        currency_obj.create(original2)

    pen = currency_obj.search([('name', '=', 'PEN'), '|', ('active', '=', True), ('active', '=', False)])
    if len(pen) > 0:
        op = {
            'name': pen.name + '-Venta',
            'currency_unit_label': pen.currency_unit_label + ' (Venta)',
            'rate_type': 'venta',
            'rate_inv': pen.rate,
            'symbol': pen.symbol,
            'rounding': pen.rounding,
            'decimal_places': pen.decimal_places,
            'currency_subunit_label': pen.currency_subunit_label,
            'position': pen.position,
            'active': True
        }
        default = currency_obj.create(op)

    env['ir.config_parameter'].sudo().set_param('module_currency_rate_live', True)
    env['ir.config_parameter'].sudo().set_param('group_multi_currency', True)

    if default:
        env.user.sudo().company_id.currency_id = default.id
    currency_obj.search([('name', '=', 'USD'), '|', ('active', '=', True), ('active', '=', False)]).active = False
    currency_obj.search([('name', '=', 'PEN'), '|', ('active', '=', True), ('active', '=', False)]).active = False
