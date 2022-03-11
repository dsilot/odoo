import datetime
from lxml import etree
from dateutil.relativedelta import relativedelta
import re
import requests
import urllib3
import logging
import json
from pytz import timezone

import requests

from odoo import api, fields, models, _
from odoo.addons.web.controllers.main import xml2json_from_elementtree
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

BANXICO_DATE_FORMAT = '%d/%m/%Y'

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'


    currency_interval_unit = fields.Selection([
        ('manually', 'Manually'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')],
        default='manually', string='Intervalo')
    currency_next_execution_date = fields.Date(string="Siguiente ejecución")
    currency_provider = fields.Selection([
        ('ecb', 'European Central Bank'),
        ('fta', 'Federal Tax Administration (Switzerland)'),
        ('banxico', 'Mexican Bank'),
        ('boc', 'Bank Of Canada'),
        ('xe_com', 'xe.com'),
        ('bnr', 'National Bank Of Romania'),
        ('mindicador', 'Chilean mindicador.cl'),
        ('bcrp', 'Bank of Peru'),
        ('provider_xmarts_peru_migo', 'Xmarts Perú / Migo')
    ], default='ecb', string='Servicio')
    xmarts_currency_provider = fields.Selection([('provider_xmarts_peru_migo', 'Xmarts Perú / Migo')],
                                                default='provider_xmarts_peru_migo', string='Servicio')
    xmarts_currency_interval_unit = fields.Selection([('daily', 'Daily')], default='daily', string='Intervalo')

    @api.model
    def run_update_currency(self):
        """ This method is called from a cron job to update currency rates.
        """
        live = self.env['ir.module.module'].search([('name', '=', 'currency_rate_live')])
        if live.state == 'installed':
            super(ResCompany, self).run_update_currency()
        else:
            records = self.search([('currency_next_execution_date', '<=', fields.Date.today())])
            if records:
                to_update = self.env['res.company']
                for record in records:
                    if record.currency_interval_unit == 'daily':
                        next_update = relativedelta(days=+1)
                    elif record.currency_interval_unit == 'weekly':
                        next_update = relativedelta(weeks=+1)
                    elif record.currency_interval_unit == 'monthly':
                        next_update = relativedelta(months=+1)
                    else:
                        record.currency_next_execution_date = False
                        continue
                    record.currency_next_execution_date = datetime.date.today() + next_update
                    to_update += record
                to_update.update_currency_rates()

    def _group_by_provider(self):
        """ Returns a dictionnary grouping the companies in self by currency
        rate provider. Companies with no provider defined will be ignored."""
        rslt = {}
        for company in self:
            if not company.currency_provider:
                continue

            if rslt.get(company.currency_provider):
                rslt[company.currency_provider] += company
            else:
                rslt[company.currency_provider] = company
        return rslt

    def update_currency_rates(self):
        ''' This method is used to update all currencies given by the provider.
        It calls the parse_function of the selected exchange rates provider automatically.

        For this, all those functions must be called _parse_xxx_data, where xxx
        is the technical name of the provider in the selection field. Each of them
        must also be such as:
            - It takes as its only parameter the recordset of the currencies
              we want to get the rates of
            - It returns a dictionary containing currency codes as keys, and
              the corresponding exchange rates as its values. These rates must all
              be based on the same currency, whatever it is. This dictionary must
              also include a rate for the base currencies of the companies we are
              updating rates from, otherwise this will result in an error
              asking the user to choose another provider.

        :return: True if the rates of all the records in self were updated
                 successfully, False if at least one wasn't.
        '''
        rslt = True
        active_currencies = self.env['res.currency'].search([])
        for (currency_provider, companies) in self._group_by_provider().items():
            parse_results = None
            parse_function = getattr(companies, '_parse_' + currency_provider + '_data')
            parse_results = parse_function(active_currencies)

            if parse_results == False:
                # We check == False, and don't use bool conversion, as an empty
                # dict can be returned, if none of the available currencies is supported by the provider
                _logger.warning('Unable to connect to the online exchange rate platform %s. The web service may be temporary down.', currency_provider)
                rslt = False
            else:
                companies._generate_currency_rates(parse_results)

        return rslt

    def _generate_currency_rates(self, parsed_data):
        for company in self:
            if company.currency_provider == 'provider_xmarts_peru_migo':
                CurrencyRate = self.env['res.currency.rate']
                Currency = self.env['res.currency']
                for rate in parsed_data:
                    name_moneda_compra = ''
                    name_moneda_venta = ''
                    currency_object_compra = None
                    currency_object_venta = None
                    if rate['moneda']=='USD':
                        name_moneda_compra = 'USD-Compra'
                        name_moneda_venta = 'USD-Venta'
                    elif rate['moneda']=='EUR':
                        name_moneda_compra = 'EUR-Compra'
                        name_moneda_venta = 'EUR-Venta'
                    elif rate['moneda']=='CAD':
                        name_moneda_compra = 'CAD-Compra'
                        name_moneda_venta = 'CAD-Venta'
                    elif rate['moneda']=='GBP':
                        name_moneda_compra = 'GBP-Compra'
                        name_moneda_venta = 'GBP-Venta'
                    elif rate['moneda']=='CHF':
                        name_moneda_compra = 'CHF-Compra'
                        name_moneda_venta = 'CHF-Venta'
                    elif rate['moneda']=='JPY':
                        name_moneda_compra = 'JPY-Compra'
                        name_moneda_venta = 'JPY-Venta'
                    elif rate['moneda']=='CNY':
                        name_moneda_compra = 'CNY-Compra'
                        name_moneda_venta = 'CNY-Venta'

                    currency_object_compra = Currency.search([('name', '=', name_moneda_compra)])
                    currency_object_venta = Currency.search([('name', '=', name_moneda_venta)])
                    if currency_object_compra != None:
                        tasa_dia_compra=CurrencyRate.search([('name','=',rate['fecha']),
                                                             ('currency_id','=',currency_object_compra.id),
                                                             ('company_id','=',company.id)])
                        if tasa_dia_compra:
                            CurrencyRate.write({
                                'rate': rate['precio_compra']
                            })
                        else:
                            CurrencyRate.create(
                                {'currency_id': currency_object_compra.id, 'rate': rate['precio_compra'], 'name': rate['fecha'],
                                'company_id': company.id})
                    else:
                        raise UserError(_('No se encontró la moneda ' + name_moneda_compra + '.'))

                    if currency_object_venta != None:
                        tasa_dia_venta = CurrencyRate.search([('name', '=', rate['fecha']),
                                                               ('currency_id', '=', currency_object_venta.id),
                                                               ('company_id', '=', company.id)])
                        if tasa_dia_venta:
                            CurrencyRate.write({
                                'rate': rate['precio_venta']
                            })
                        else:
                            CurrencyRate.create(
                                {'currency_id': currency_object_venta.id, 'rate': rate['precio_venta'], 'name': rate['fecha'],
                                'company_id': company.id})
                    else:
                        raise UserError(_('No se encontró la moneda ' + name_moneda_venta + '.'))

            else:
                return super(ResCompany, self)._generate_currency_rates(parsed_data)

    def _parse_provider_xmarts_peru_migo_data(self, available_currencies):
        bcrp_date_format_url = '%Y-%m-%d'
        bcrp_date_format_res = '%d.%b.%y'
        result = {}
        # token_setting = self.env['res.config.settings'].search([], limit=1).xmpe_token
        token_setting = self.env["ir.config_parameter"].sudo().get_param("xmpe_token")
        if not token_setting:
            _logger.warning('Error obteniendo TOKEN')
        else:
            _logger.warning('OK TOKEN: %s' % token_setting)

        if token_setting:
            headers = {
                'Content-Type': 'application/json',
            }
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            if self.env.context.get('consulta_migo_exchange'):
                first_pe_str = (self.env.context.get('inicial_date')).strftime(bcrp_date_format_url)
                second_pe_str = (self.env.context.get('end_date')).strftime(bcrp_date_format_url)
                url = 'https://api.migo.pe/api/v1/exchange?token=%s&fecha_inicio=%s&fecha_fin=%s' % (token_setting,first_pe_str,second_pe_str)
            else:
                url = 'https://api.migo.pe/api/v1/exchange/latest?token=%s' % (token_setting)
            try:
                res = requests.post(url, headers=headers, verify=False)
                res.raise_for_status()
                series = res.json()
                if series.get('data') == None and series.get('success'):
                    data = {
                            'fecha': series['fecha'],
                            'moneda': series['moneda'],
                            'precio_compra': series['precio_compra'],
                            'precio_venta': series['precio_venta']
                            }
                    series['data'] = [data]
                    return series['data']
                elif series.get('data'):
                    return series['data']

            except requests.exceptions.ConnectionError as e:
                _logger.error("Error al consultar las tasa de cambio desde Migo. Detalles: " + str(e))
                raise UserError(_('Error al conectarse al proveedor de servicio.'))

    def run_update_currency_hours(self):
        obj = self.env.user.company_id.sudo()
        parse = obj._parse_provider_xmarts_peru_migo_data(available_currencies=[])
        obj._generate_currency_rates(parse)
        _logger.info("Info: Se ha ejecutado la consulta de tipo de cambio planificada cada 6 horas.")


