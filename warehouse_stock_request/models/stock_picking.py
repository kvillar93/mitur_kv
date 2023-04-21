# -*- coding: utf-8 -*-

import re
from markupsafe import Markup
from odoo import api, fields, Command, models, _
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero, float_repr, float_compare, is_html_empty
from odoo.tools.misc import clean_context, format_date

class HrExpense(models.Model):
    _inherit = "hr.expense.sheet"
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('rev_rrhh', 'Revisado RRHH'),
        ('apr_rrhh', 'Aprobado RRHH'),
        ('adm_val', 'Validado Vice ADM'),
        ('apr_adm', 'Aprobado Vice ADM'),
        ('post', 'Posted'),
        ('done', 'Pagado'),
        ('aut_fin', 'Autorizado Financiero'),
        ('rev_ad', 'Revisión Auditoría'),
        ('firma_orden_pago_vice_adm', 'Firma Vice ADM'),
        ('desemb', 'Desembolso'),
        ('cancel', 'Refused')
    ], string='Status', index=True, readonly=True, tracking=True, copy=False, default='draft', required=True)
    
    
    def button_rev_rrhh(self):
        for rec in self:
            rec.write({'state':'rev_rrhh'})
    
    def button_apr_rrhh(self):
        for rec in self:
            rec.write({'state':'apr_rrhh'})
    
    def button_adm_val(self):
        for rec in self:
            rec.write({'state':'adm_val'})
            
    def button_apr_adm(self):
        for rec in self:
            rec.write({'state':'apr_adm'})
    
    def button_aut_fin(self):
        for rec in self:
            rec.write({'state':'aut_fin'})
            
    def button_rev_ad(self):
        for rec in self:
            rec.write({'state':'rev_ad'})

    def button_firma_orden_pago_vice_adm(self):
        for rec in self:
            rec.write({'state':'firma_orden_pago_vice_adm'})
    
    def button_desemb(self):
        for rec in self:
            rec.write({'state':'desemb'})
            
    def action_sheet_move_create(self):
        samples = self.mapped('expense_line_ids.sample')
        if samples.count(True):
            if samples.count(False):
                raise UserError(_("You can't mix sample expenses and regular ones"))
            self.write({'state': 'post'})
            return 

        if any(sheet.state != 'apr_adm' for sheet in self):
            raise UserError(_("Solo puede generar las entradas de libro para viaticos aprobados por la Vice Administracion. Estado: %s", self.state))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Specify expense journal to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.company.currency_id).rounding))
        res = expense_line_ids.with_context(clean_context(self.env.context)).action_move_create()

        paid_expenses_company = self.filtered(lambda m: m.payment_mode == 'company_account')
        paid_expenses_company.write({'state': 'done', 'amount_residual': 0.0, 'payment_state': 'paid'})

        paid_expenses_employee = self - paid_expenses_company
        paid_expenses_employee.write({'state': 'post'})

        self.activity_update()
        return res




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
    def onchange_picking_type(self):
        ctx = self._context.copy()
        if not ctx.get('is_warehouse_stock_request'):
            return super(StockPicking, self).onchange_picking_type()
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