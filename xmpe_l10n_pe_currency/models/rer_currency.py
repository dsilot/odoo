# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    name = fields.Char(size=10)
    rate_type = fields.Selection([
        ('compra', 'Compra'),
        ('venta', 'Venta'),
    ], string='Tipo', readonly=True)

    rate_inv = fields.Float('Tipo de cambio', compute='_compute_current_rate', digits=0)

    @api.depends('rate_ids.rate')
    def _compute_current_rate(self):
        super(ResCurrency, self)._compute_current_rate()
        for currency in self:
            if currency.rate > 0:
                currency.rate_inv = 1 / currency.rate
            else:
                currency.rate_inv = 1
                currency.rate = 1


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    rate_inv = fields.Float('Tipo de cambio',readonly=True, digits=0)

    @api.model
    def create(self, vals):
        if vals.get('rate'):
            vals['rate_inv'] = float(vals['rate'])
            vals['rate'] = 1 / float(vals['rate'])
        rate = super(ResCurrencyRate, self).create(vals)
        return rate
