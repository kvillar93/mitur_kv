from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError


class IrModelFields(models.Model):
    _inherit = "ir.model.fields"

    def _add_manual_fields(self, model):
        res = super()._add_manual_fields(model)
        self.env["bi.sql.view"].check_manual_fields(model)
        return res

class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.constrains('check_number', 'journal_id')
    def _constrains_check_number(self):
        payment_checks = self.filtered('check_number')
    
        if not payment_checks or self.batch_payment_id:
            return
        for payment_check in payment_checks:
            if not payment_check.check_number.isdecimal():
                raise ValidationError(_('Check numbers can only consist of digits'))
        self.flush()
        self.env.cr.execute("""
            SELECT payment.check_number, move.journal_id
              FROM account_payment payment
              JOIN account_move move ON move.id = payment.move_id
              JOIN account_journal journal ON journal.id = move.journal_id,
                   account_payment other_payment
              JOIN account_move other_move ON other_move.id = other_payment.move_id
             WHERE payment.check_number::BIGINT = other_payment.check_number::BIGINT
               AND move.journal_id = other_move.journal_id
               AND payment.id != other_payment.id
               AND payment.id IN %(ids)s
               AND move.state = 'posted'
               AND other_move.state = 'posted'
               AND payment.check_number IS NOT NULL
               AND other_payment.check_number IS NOT NULL
        """, {
            'ids': tuple(payment_checks.ids),
        })
        res = self.env.cr.dictfetchall()
        if res:
            raise ValidationError(_(
                'The following numbers are already used:\n%s',
                '\n'.join(_(
                    '%(number)s in journal %(journal)s',
                    number=r['check_number'],
                    journal=self.env['account.journal'].browse(r['journal_id']).display_name,
                ) for r in res)
            ))