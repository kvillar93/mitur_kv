import logging

_logger = logging.getLogger(__name__)

# 2 :  imports of odoo [Imports of odoo]

import odoo
from odoo import api, fields, models, _  # alphabetically ordered
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from . import number_to_word




class IssuesBankChequeHistory(models.Model):
    # Private attributes
    _inherit = "issued.bank.cheque.history"


    def print_cheque(self):
        self.ensure_one()
        if self.issued:
            raise UserError(
                _(
                    "Cheque has been already printed with Cheque number %s"
                    % self.cheque_number
                )
            )
        # if not self.customer_id or not self.issue_date or self.amount <= 0:
        #     raise UserError(_("One of the field is missing may be Customer, Date or Amount."))
        wizard_id = self.env["invoice.print.bank.cheque.wizard"].create(
            {
                "partner_id": self.customer_id.id,
                "cheque_book_id": self.bank_cheque_book_id.id,
                "cheque_history_id": self.id,
                "pay_name_line1": self.customer_id.name
                if self.customer_id
                else self.paid_to,
                "amount": self.amount,
            }
        )
        wizard_id.amount_in_words = number_to_word.to_word(
                wizard_id.amount, wizard_id.currency_id.name)
        return {
            "name": _("Print Cheque"),
            "view_mode": "form",
            "view_id": False,
            "res_model": "invoice.print.bank.cheque.wizard",
            "res_id": wizard_id.id,
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "target": "new",
        }


class InvoicePrintBankChequeWizard(models.TransientModel):
    _inherit = "invoice.print.bank.cheque.wizard"


    @api.model
    def _get_amount_in_words(self):
        amount_total_words = ""
        if self._context.get("active_id"):
            if self._context.get("active_model") == "account.move":
                active_obj = self.env["account.move"].browse(
                    self._context.get("active_id")
                )
                amount_total_words = number_to_word.to_word(
                active_obj.amount_total, active_obj.currency_id.name)
                
            if self._context.get("active_model") == "account.payment":
                active_obj = self.env["account.payment"].browse(
                    self._context.get("active_id")
                )
                amount_total_words = number_to_word.to_word(
                active_obj.amount, active_obj.currency_id.name)
                
        return amount_total_words

    @api.onchange("amount")
    def onchange_amount(self):
        if self.currency_id:
            self.amount_in_words_line2 = False
            self.amount_in_words = amount_total_words = number_to_word.to_word(
                self.amount, self.currency_id.name)
            
            self.set_amount_lines_in_word()

   