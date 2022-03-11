#! -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import UserError
from ast import literal_eval
import datetime
from dateutil import rrule

class WizardConsultaMigoExchange(models.TransientModel):
    _name = 'wizard.consulta.migo.exchange'

    inicial_date = fields.Date(string='Fecha inicial',required=True)
    end_date = fields.Date(string='Fecha final',required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda s: s.env.company.id)

    def consulta_migo_exchange(self):
        for wizard in self:
            if wizard.inicial_date > wizard.end_date:
                raise UserError(_('La fecha inicial debe ser menor que la fecha final.'))
            elif rrule.rrule(rrule.MONTHLY, dtstart=wizard.inicial_date, until=wizard.end_date).count() > 6:
                raise UserError(_('No puede existir una diferencia entre la fecha inicial y final mayor a 6 meses.'))
            else:
                action = self.env["ir.actions.actions"]._for_xml_id("xmpe_l10n_pe_currency.action_consulta_migo_exchange")
                context = literal_eval(action['context'])
                context.update(self.env.context)
                context['inicial_date'] = wizard.inicial_date
                context['end_date'] = wizard.end_date
                self.env.context = context
                self.company_id.update_currency_rates()




