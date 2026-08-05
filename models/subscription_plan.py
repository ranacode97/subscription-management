from odoo import models, fields, api


class SubscriptionPlan(models.Model):
    _name = 'subscription.plan'
    _description = 'Subscription Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    name = fields.Char(string='Plan Name', required=True, tracking=True)
    code = fields.Char(string='Plan Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)

    description = fields.Html(string='Description')
    billing_cycle = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
        ('biennial', 'Biennial (2 Years)'),
    ], string='Billing Cycle', required=True, default='monthly', tracking=True)

    duration_months = fields.Integer(
        string='Duration (Months)',
        compute='_compute_duration_months',
        store=True,
    )

    price = fields.Float(string='Price', required=True, digits=(10, 2), tracking=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id,
    )

    max_domains = fields.Integer(string='Max Domains Allowed', default=1)
    max_storage_gb = fields.Float(string='Max Storage (GB)', default=1.0)
    max_users = fields.Integer(string='Max Users', default=1)
    max_bandwidth_gb = fields.Float(string='Max Bandwidth (GB)', default=10.0)

    # Features
    feature_ssl = fields.Boolean(string='SSL Certificate', default=True)
    feature_backup = fields.Boolean(string='Auto Backup', default=False)
    feature_support = fields.Selection([
        ('email', 'Email Support'),
        ('priority', 'Priority Support'),
        ('dedicated', 'Dedicated Support'),
    ], string='Support Level', default='email')

    subscription_count = fields.Integer(
        string='Subscriptions',
        compute='_compute_subscription_count',
    )

    color = fields.Integer(string='Color')

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Plan code must be unique!'),
        ('price_positive', 'CHECK(price >= 0)', 'Price must be positive!'),
    ]

    @api.depends('billing_cycle')
    def _compute_duration_months(self):
        cycle_map = {
            'monthly': 1,
            'quarterly': 3,
            'semi_annual': 6,
            'annual': 12,
            'biennial': 24,
        }
        for record in self:
            record.duration_months = cycle_map.get(record.billing_cycle, 1)

    def _compute_subscription_count(self):
        for record in self:
            record.subscription_count = self.env['subscription.subscription'].search_count([
                ('plan_id', '=', record.id),
            ])

    def action_view_subscriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Subscriptions - {self.name}',
            'res_model': 'subscription.subscription',
            'view_mode': 'tree,form,kanban',
            'domain': [('plan_id', '=', self.id)],
            'context': {'default_plan_id': self.id},
        }
