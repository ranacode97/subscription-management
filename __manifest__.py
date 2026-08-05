{
    'name': 'Subscription Management',
    'version': '17.0.1.0.0',
    'category': 'Sales/Subscriptions',
    'summary': 'Manage subscriptions with start/expiry dates, domains, and automated renewals',
    'description': """
        Subscription Management Module
        ===============================
        Features:
        - Subscription lifecycle management (draft → active → expired → cancelled)
        - Subscription plans with flexible billing cycles
        - Domain management linked to subscriptions
        - Automated expiry detection via cron jobs
        - Email notifications for upcoming expirations
        - Renewal wizard for quick renewals
        - Dashboard with Kanban, List, and Form views
        - Reporting and analytics
    """,
    'author': 'Custom',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'contacts'],
    'data': [
        'security/subscription_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/cron_data.xml',
        'data/mail_template_data.xml',
        'wizard/subscription_renew_views.xml',
        'views/subscription_plan_views.xml',
        'views/subscription_views.xml',
        'views/subscription_domain_views.xml',
        'views/menu_views.xml',
        'report/subscription_report_views.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
