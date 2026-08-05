from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class Subscription(models.Model):
    _name = 'subscription.subscription'
    _description = 'Subscription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'reference'

    # ── Core Fields ──────────────────────────────────────────
    reference = fields.Char(
        string='Reference', required=True, copy=False,
        readonly=True, default='New',
    )
    name = fields.Char(string='Subscription Name', required=True, tracking=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        tracking=True, index=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one(
        'res.users', string='Salesperson',
        default=lambda self: self.env.user, tracking=True,
    )
    plan_id = fields.Many2one(
        'subscription.plan', string='Subscription Plan',
        required=True, tracking=True,
    )
    currency_id = fields.Many2one(
        related='plan_id.currency_id', store=True,
    )

    # ── Dates ────────────────────────────────────────────────
    date_start = fields.Date(
        string='Start Date', required=True,
        default=fields.Date.context_today, tracking=True,
    )
    date_end = fields.Date(
        string='Expiry Date', compute='_compute_date_end',
        store=True, tracking=True,
    )
    date_next_invoice = fields.Date(string='Next Invoice Date', tracking=True)
    days_to_expire = fields.Integer(
        string='Days to Expire', compute='_compute_days_to_expire',
        store=True,
    )

    # ── Financial ────────────────────────────────────────────
    recurring_price = fields.Float(
        related='plan_id.price', string='Recurring Price', store=True,
    )
    total_invoiced = fields.Float(
        string='Total Invoiced', digits=(10, 2), default=0.0,
    )

    # ── Status ───────────────────────────────────────────────
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('active', 'Active'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, index=True)

    # ── Related Records ──────────────────────────────────────
    domain_ids = fields.One2many(
        'subscription.domain', 'subscription_id', string='Domains',
    )
    domain_count = fields.Integer(
        string='Domain Count', compute='_compute_domain_count',
    )

    # ── Renewal ──────────────────────────────────────────────
    is_auto_renew = fields.Boolean(
        string='Auto Renew', default=True, tracking=True,
    )
    renewal_count = fields.Integer(string='Times Renewed', default=0)

    # ── Notes ────────────────────────────────────────────────
    notes = fields.Html(string='Internal Notes')
    tag_ids = fields.Many2many('subscription.tag', string='Tags')

    # ── Display ──────────────────────────────────────────────
    color = fields.Integer(string='Color')
    kanban_state = fields.Selection([
        ('normal', 'In Progress'),
        ('done', 'Ready'),
        ('blocked', 'Blocked'),
    ], string='Kanban State', default='normal')

    _sql_constraints = [
        ('reference_unique', 'UNIQUE(reference)', 'Subscription reference must be unique!'),
    ]

    # ── Computed Fields ──────────────────────────────────────
    @api.depends('date_start', 'plan_id.duration_months')
    def _compute_date_end(self):
        for rec in self:
            if rec.date_start and rec.plan_id:
                rec.date_end = rec.date_start + relativedelta(
                    months=rec.plan_id.duration_months
                )
            else:
                rec.date_end = False

    @api.depends('date_end')
    def _compute_days_to_expire(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.date_end:
                rec.days_to_expire = (rec.date_end - today).days
            else:
                rec.days_to_expire = 0

    def _compute_domain_count(self):
        for rec in self:
            rec.domain_count = len(rec.domain_ids)

    # ── Constraints ──────────────────────────────────────────
    @api.constrains('domain_ids', 'plan_id')
    def _check_domain_limit(self):
        for rec in self:
            if rec.plan_id and len(rec.domain_ids) > rec.plan_id.max_domains:
                raise ValidationError(
                    _('This plan allows a maximum of %d domains. '
                      'You have %d domains assigned.') %
                    (rec.plan_id.max_domains, len(rec.domain_ids))
                )

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end <= rec.date_start:
                raise ValidationError(_('Expiry date must be after the start date.'))

    # ── CRUD Overrides ───────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'subscription.subscription'
                ) or 'New'
        return super().create(vals_list)

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancelled'):
                raise UserError(
                    _('You can only delete subscriptions in Draft or Cancelled state.')
                )
        return super().unlink()

    # ── State Machine ────────────────────────────────────────
    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft subscriptions can be confirmed.'))
            rec.state = 'confirm'
            rec.date_next_invoice = rec.date_start
            rec.message_post(body=_('Subscription confirmed.'))

    def action_activate(self):
        for rec in self:
            if rec.state not in ('confirm', 'expired'):
                raise UserError(_('Only confirmed or expired subscriptions can be activated.'))
            rec.state = 'active'
            rec.message_post(body=_('Subscription activated.'))

    def action_cancel(self):
        for rec in self:
            if rec.state == 'cancelled':
                raise UserError(_('Subscription is already cancelled.'))
            rec.state = 'cancelled'
            # Deactivate all domains
            rec.domain_ids.write({'state': 'inactive'})
            rec.message_post(body=_('Subscription cancelled.'))

    def action_set_to_draft(self):
        for rec in self:
            if rec.state != 'cancelled':
                raise UserError(_('Only cancelled subscriptions can be reset to draft.'))
            rec.state = 'draft'
            rec.message_post(body=_('Subscription reset to draft.'))

    def action_renew(self):
        """Open the renewal wizard."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Renew Subscription'),
            'res_model': 'subscription.renew.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_subscription_id': self.id,
                'default_plan_id': self.plan_id.id,
            },
        }

    def action_view_domains(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Domains'),
            'res_model': 'subscription.domain',
            'view_mode': 'tree,form',
            'domain': [('subscription_id', '=', self.id)],
            'context': {'default_subscription_id': self.id},
        }

    # ── Cron Methods ─────────────────────────────────────────
    @api.model
    def _cron_check_expiring_subscriptions(self):
        """Mark subscriptions expiring within 30 days."""
        today = fields.Date.context_today(self)
        threshold = today + relativedelta(days=30)

        # Mark expiring soon
        expiring = self.search([
            ('state', '=', 'active'),
            ('date_end', '<=', threshold),
            ('date_end', '>', today),
        ])
        expiring.write({'state': 'expiring_soon'})
        for sub in expiring:
            sub.message_post(
                body=_('⚠️ Subscription expires in %d days.') % sub.days_to_expire
            )
        _logger.info('Marked %d subscriptions as expiring soon.', len(expiring))

        # Mark expired
        expired = self.search([
            ('state', 'in', ('active', 'expiring_soon')),
            ('date_end', '<=', today),
        ])
        expired.write({'state': 'expired'})
        for sub in expired:
            sub.domain_ids.write({'state': 'inactive'})
            sub.message_post(body=_('❌ Subscription has expired.'))
        _logger.info('Marked %d subscriptions as expired.', len(expired))

    @api.model
    def _cron_auto_renew_subscriptions(self):
        """Auto-renew eligible subscriptions."""
        today = fields.Date.context_today(self)
        to_renew = self.search([
            ('state', 'in', ('expired', 'expiring_soon')),
            ('is_auto_renew', '=', True),
            ('date_end', '<=', today),
        ])
        for sub in to_renew:
            sub.write({
                'date_start': today,
                'state': 'active',
                'renewal_count': sub.renewal_count + 1,
            })
            sub.domain_ids.write({'state': 'active'})
            sub.message_post(
                body=_('🔄 Subscription auto-renewed (renewal #%d).') % sub.renewal_count
            )
        _logger.info('Auto-renewed %d subscriptions.', len(to_renew))


class SubscriptionTag(models.Model):
    _name = 'subscription.tag'
    _description = 'Subscription Tag'
    _order = 'name'

    name = fields.Char(string='Tag Name', required=True)
    color = fields.Integer(string='Color')

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Tag name must be unique!'),
    ]
