# -*- coding: utf-8 -*-
{
    'name': "Tipo de cambio - Perú",

    'summary': """
        Funcionalidad Tipo de cambio para Perú.""",

    'description': """
        
    """,

    'author': "XMarts",
    'website': "https://www.xmarts.com",

    'category': 'Account',
    'version': '1.1.20211002',
    'depends': [
        'xmpe_migo_api_settings',
        'account',
    ],

    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data
        'data/ir_cron.xml',

        # Views
        'wizard/wizard_consulta_migo_exchange_view.xml',
        'views/res_config_settings_views.xml',
        'views/res_currency_view.xml',

        # Menus
        #'views/menu_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
}
