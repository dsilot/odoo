# -*- coding: utf-8 -*-

from ast import literal_eval
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo import api, SUPERUSER_ID


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_multi_currency = fields.Boolean()
    module_currency_rate_live = fields.Boolean()

    currency_interval_unit = fields.Selection(related="company_id.currency_interval_unit", readonly=False)
    currency_provider = fields.Selection(related="company_id.currency_provider", readonly=False)
    xmarts_currency_provider = fields.Selection(related="company_id.xmarts_currency_provider", readonly=False)
    xmarts_currency_interval_unit= fields.Selection(related="company_id.xmarts_currency_interval_unit", readonly=False)
    currency_next_execution_date = fields.Date(related="company_id.currency_next_execution_date", readonly=False)

    @api.onchange('currency_provider')
    def change_currency_provider(self):
        modulo_currency_rate_live = self.env['ir.module.module'].search([('name','=','currency_rate_live')])
        if modulo_currency_rate_live:
            if modulo_currency_rate_live.state != 'installed':
                self.env['ir.config_parameter'].sudo().set_param('module_currency_rate_live', False)
                self.currency_provider = self.xmarts_currency_provider
                self.currency_interval_unit = self.xmarts_currency_interval_unit
            else:
                self.env['ir.config_parameter'].sudo().set_param('module_currency_rate_live', True)
        else:
            self.env['ir.config_parameter'].sudo().set_param('module_currency_rate_live', False)
            self.currency_provider = self.xmarts_currency_provider
            self.currency_interval_unit = self.xmarts_currency_interval_unit

    def update_currency_rates_manually(self):
        self.ensure_one()
        if not (self.company_id.update_currency_rates()):
            raise UserError(_('Unable to connect to the online exchange rate platform. The web service may be temporary down. Please try again in a moment.'))

    @api.model
    def get_values(self):
        res = super().get_values()
        res.update(
            group_multi_currency=self.env["ir.config_parameter"].sudo().get_param("group_multi_currency"),
            module_currency_rate_live=self.env["ir.config_parameter"].sudo().get_param("module_currency_rate_live"),
        )
        return res

    def set_values(self):
        super().set_values()
        for record in self:
            self.env['ir.config_parameter'].sudo().set_param("group_multi_currency",
                                                             record.group_multi_currency)
            self.env['ir.config_parameter'].sudo().set_param("module_currency_rate_live",
                                                             record.module_currency_rate_live)
