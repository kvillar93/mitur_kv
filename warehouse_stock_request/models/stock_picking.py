# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

class AccountTax(models.Model):
    _inherit = "account.tax"
    
    tax_partner_id = fields.Many2one('res.partner', 'Proveedor de Impuesto Relacionado')

class AcountMove(models.Model):
    _inherit = "account.move"
    
    retention_payment = fields.Many2many('account.payment', 'dgii_payments_rel', 'move_dgii_id', 'pay_id',
                                   string='Pagos DGII Relacionados a Factura')

    
    
class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    is_dgii_payment = fields.Boolean(string="Es pago de DGII", store=True,default=False)
    
    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):

            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                if len(liquidity_lines) != 1:
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "include one and only one outstanding payments/receipts account.",
                        move.display_name,
                    ))

                if len(counterpart_lines) != 1 and pay.is_dgii_payment == False:
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "include one and only one receivable/payable account (with an exception of "
                        "internal transfers).",
                        move.display_name,
                    ))

                if writeoff_lines and len(writeoff_lines.account_id) != 1:
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, "
                        "all optional journal items must share the same account.",
                        move.display_name,
                    ))

                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same currency.",
                        move.display_name,
                    ))

                if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same partner.",
                        move.display_name,
                    ))

                if counterpart_lines.account_id.user_type_id.type == 'receivable':
                    partner_type = 'customer'
                else:
                    partner_type = 'supplier'

                liquidity_amount = liquidity_lines.amount_currency

                move_vals_to_write.update({
                    'currency_id': liquidity_lines.currency_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                payment_vals_to_write.update({
                    'amount': abs(liquidity_amount),
                    'partner_type': partner_type,
                    'currency_id': liquidity_lines.currency_id.id,
                    'destination_account_id': counterpart_lines.account_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                if liquidity_amount > 0.0:
                    payment_vals_to_write.update({'payment_type': 'inbound'})
                elif liquidity_amount < 0.0:
                    payment_vals_to_write.update({'payment_type': 'outbound'})

            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))

class PaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"
    
    def _create_reconciled_taxes_move(self, invoices):

        aml_mapping = {}
        if invoices:
            journal = self._get_reconciled_payment_move_journal()
            partner_id = invoices[0].partner_id

            move = (
                self.env["account.move"]
                .with_context(default_move_type="entry")
                .create(
                    {
                        "ref": " ".join(
                            [
                                i.l10n_do_fiscal_number
                                for i in invoices
                                if i.l10n_do_fiscal_number
                            ]
                        ),
                        "journal_id": journal,
                        "date": self.payment_date,
                    }
                )
            )

            move_line_vals = []
            for line in self.l10n_do_payments_invoice_ids:
                for tax in line.tax_ids:
                    debit, amount, amount_currency = self._get_move_amounts(line, tax)
                    move_line_vals.extend(
                        [
                            (
                                0,
                                0,
                                {
                                    "move_id": move.id,
                                    "name": tax.name,
                                    "account_id": self._get_tax_account(tax),
                                    "debit": amount
                                    if line.invoice_id.move_type == "out_invoice"
                                    else 0.0,
                                    "credit": amount
                                    if line.invoice_id.move_type == "in_invoice"
                                    else 0.0,
                                    "journal_id": journal,
                                    "partner_id": partner_id.id,
                                },
                            ),
                            (
                                0,
                                0,
                                {
                                    "move_id": move.id,
                                    "name": tax.name,
                                    "account_id": self._get_invoice_reconcile_move_account(
                                        line.invoice_id
                                    ),
                                    "debit": amount
                                    if line.invoice_id.move_type == "in_invoice"
                                    else 0.0,
                                    "credit": amount
                                    if line.invoice_id.move_type == "out_invoice"
                                    else 0.0,
                                    "journal_id": journal,
                                    "partner_id": partner_id.id,
                                    "l10n_do_reconcile_invoice_id": line.invoice_id.id,
                                },
                            ),
                        ]
                    )

            move.line_ids = move_line_vals
            for ml in move.line_ids.filtered(
                lambda l: l.l10n_do_reconcile_invoice_id and not l.reconciled
            ):
                if ml.l10n_do_reconcile_invoice_id not in aml_mapping:
                    aml_mapping[ml.l10n_do_reconcile_invoice_id] = [ml.id]
                else:
                    aml_mapping[ml.l10n_do_reconcile_invoice_id].append(ml.id)

            move._post()

        return aml_mapping
    
    
    def _prepare_tax_payment(self, amount,tax):
        vals = {
                'date': self.payment_date,
                'amount': amount,
                'payment_type': 'outbound',
                'partner_type': self.partner_type,
                'ref': self.communication,
                'journal_id': self.journal_id.id,
                'currency_id': self.currency_id.id,
                'partner_id': tax.tax_partner_id.id,
                'partner_bank_id': self.partner_bank_id.id,
                'payment_method_line_id': self.payment_method_line_id.id,
                'is_dgii_payment':True,
                # 'destination_account_id': self._get_tax_account(tax),
            }
        return vals
    
    def _create_payments(self):


        if self.l10n_do_reconcile_taxes and self.payment_type == 'outbound':
            invoices = self.l10n_do_payments_invoice_ids.mapped("invoice_id")

        
            tax_payment = self.env['account.payment']
        
            for line in self.l10n_do_payments_invoice_ids:
                    for tax in line.tax_ids:
                        debit, amount, amount_currency = self._get_move_amounts(line, tax)

                        payment_vals = self._prepare_tax_payment(amount,tax)
                        
                        payment = self.env['account.payment'].sudo().create(payment_vals)
                        
                        for line in payment.move_id.line_ids:
                            if line.debit > 0:
                                line.account_id = self._get_tax_account(tax)
                                
                        
                        payment.action_post()

                        tax_payment += payment

            if len(tax_payment) > 0:
                for move in self.line_ids.filtered(lambda x: x.move_id.move_type != 'entry'):
                    move.move_id.write({'retention_payment':[(6,0,tax_payment.ids)]})
                                
                

        return super(PaymentRegister, self)._create_payments()



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    stock_request_id = fields.Many2one(
        'custom.warehouse.stock.request',
        string="Warehouse Stock Request",
        copy=True,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    @api.onchange('picking_type_id', 'partner_id')
    def _onchange_picking_type(self):
        ctx = self._context.copy()
        if not ctx.get('is_warehouse_stock_request'):
            return super(StockPicking, self)._onchange_picking_type()
        # if self.picking_type_id and self.state == 'draft' and not ctx.get('is_warehouse_stock_request'):
        #     self = self.with_company(self.company_id)
        #     if self.picking_type_id.default_location_src_id:
        #         location_id = self.picking_type_id.default_location_src_id.id
        #     elif self.partner_id:
        #         location_id = self.partner_id.property_stock_supplier.id
        #     else:
        #         customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()

        #     if self.picking_type_id.default_location_dest_id:
        #         location_dest_id = self.picking_type_id.default_location_dest_id.id
        #     elif self.partner_id:
        #         location_dest_id = self.partner_id.property_stock_customer.id
        #     else:
        #         location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()

        #     self.location_id = location_id
        #     self.location_dest_id = location_dest_id
        #     (self.move_lines | self.move_ids_without_package).update({
        #         "picking_type_id": self.picking_type_id,
        #         "company_id": self.company_id,
        #     })

        if self.partner_id and self.partner_id.picking_warn:
            if self.partner_id.picking_warn == 'no-message' and self.partner_id.parent_id:
                partner = self.partner_id.parent_id
            elif self.partner_id.picking_warn not in ('no-message', 'block') and self.partner_id.parent_id.picking_warn == 'block':
                partner = self.partner_id.parent_id
            else:
                partner = self.partner_id
            if partner.picking_warn != 'no-message':
                if partner.picking_warn == 'block':
                    self.partner_id = False
                return {'warning': {
                    'title': ("Warning for %s") % partner.name,
                    'message': partner.picking_warn_msg
                }}