from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class SubscriptionDomain(models.Model):
    _name = 'subscription.domain'
    _description = 'Subscription Domain'
    _inherit = ['mail.thread']
    _order = 'is_primary desc, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Domain Name', required=True, tracking=True,
        help='e.g. example.com',
    )
    subscription_id = fields.Many2one(
        'subscription.subscription', string='Subscription',
        required=True, ondelete='cascade', index=True,
    )
    partner_id = fields.Many2one(
        related='subscription_id.partner_id', store=True,
        string='Customer',
    )

    is_primary = fields.Boolean(string='Primary Domain', default=False)

    state = fields.Selection([
        ('pending', 'Pending Setup'),
        ('propagating', 'DNS Propagating'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
    ], string='Status', default='pending', tracking=True)

    # DNS & Technical
    dns_provider = fields.Char(string='DNS Provider')
    ip_address = fields.Char(string='IP Address')
    nameserver_1 = fields.Char(string='Nameserver 1')
    nameserver_2 = fields.Char(string='Nameserver 2')

    # SSL
    ssl_enabled = fields.Boolean(string='SSL Enabled', default=False)
    ssl_expiry_date = fields.Date(string='SSL Expiry Date')
    ssl_issuer = fields.Char(string='SSL Issuer')

    # Registration
    registration_date = fields.Date(string='Registration Date')
    expiry_date = fields.Date(
        string='Domain Expiry Date',
        related='subscription_id.date_end', store=True,
    )
    registrar = fields.Char(string='Domain Registrar')

    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('domain_unique', 'UNIQUE(name)', 'This domain is already registered in the system!'),
    ]

    @api.constrains('name')
    def _check_domain_format(self):
        domain_regex = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)'
            r'+[a-zA-Z]{2,}$'
        )
        for rec in self:
            if rec.name and not domain_regex.match(rec.name):
                raise ValidationError(
                    _('"%s" is not a valid domain name. '
                      'Expected format: example.com') % rec.name
                )

    @api.constrains('is_primary', 'subscription_id')
    def _check_single_primary(self):
        for rec in self:
            if rec.is_primary:
                other_primary = self.search([
                    ('subscription_id', '=', rec.subscription_id.id),
                    ('is_primary', '=', True),
                    ('id', '!=', rec.id),
                ])
                if other_primary:
                    raise ValidationError(
                        _('A subscription can only have one primary domain.')
                    )

    def action_activate(self):
        self.write({'state': 'active'})

    def action_deactivate(self):
        self.write({'state': 'inactive'})

    def action_set_propagating(self):
        self.write({'state': 'propagating'})
