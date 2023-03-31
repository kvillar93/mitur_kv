# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

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