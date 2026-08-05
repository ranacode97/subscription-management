from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta


class SubscriptionRenewWizard(models.TransientModel):
    _name = 'subscription.renew.wizard'
    _description = 'Subscription Renewal Wizard'

    subscription_id = fields.Many2one(
        'subscription.subscription', string='Subscription',
        required=True, readonly=True,
    )
    plan_id = fields.Many2one(
        'subscription.plan', string='New Plan',
        required=True,
    )
    new_start_date = fields.Date(
        string='New Start Date', required=True,
        default=fields.Date.context_today,
    )
    new_end_date = fields.Date(
        string='New End Date',
        compute='_compute_new_end_date',
    )

    @api.depends('new_start_date', 'plan_id')
    def _compute_new_end_date(self):
        for rec in self:
            if rec.new_start_date and rec.plan_id:
                rec.new_end_date = rec.new_start_date + relativedelta(
                    months=rec.plan_id.duration_months
                )
            else:
                rec.new_end_date = False

    def action_renew(self):
        self.ensure_one()
        sub = self.subscription_id
        sub.write({
            'plan_id': self.plan_id.id,
            'date_start': self.new_start_date,
            'state': 'active',
            'renewal_count': sub.renewal_count + 1,
        })
        sub.domain_ids.filtered(
            lambda d: d.state == 'inactive'
        ).write({'state': 'active'})
        sub.message_post(
            body=_('🔄 Subscription renewed with plan "%s" until %s (renewal #%d).') % (
                self.plan_id.name, self.new_end_date, sub.renewal_count
            )
        )
        return {'type': 'ir.actions.act_window_close'}
