# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import models,fields,api
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def _website_product_id_change(self, order_id, product_id, qty=0):
        res = super(SaleOrder, self)._website_product_id_change(order_id, product_id, qty)
        if self._context.get('rental_vals'):
            rental_vals = self._context.get('rental_vals')
            tenure_uom = int(rental_vals.get('tenure_uom')) if rental_vals.get('tenure_uom') else False
            tenure_value = float(rental_vals.get('tenure_value')) if rental_vals.get('tenure_value') else False
            tenure_price = float(rental_vals.get('tenure_price')) if rental_vals.get('tenure_price') else False
            product = self.env['product.product'].browse(product_id)
            if product and product.rental_ok and tenure_uom:
                vals = {
                    'is_rental_order': True,
                    'price_unit': tenure_price,
                    'rental_uom_id': tenure_uom,
                    'rental_tenure': tenure_value,
                    'unit_security_amount': product.security_amount,
                }
                res.update(vals)
        return res

    @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, attributes=None, **kwargs):
        flag = 0
        if line_id:
            line_obj =  self.env['sale.order.line'].browse(line_id)
            if line_obj and line_obj.is_rental_order:
                flag = 1
                tenure_rent_price = line_obj.price_unit

        res = super(SaleOrder, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)

        if res.get('line_id') and flag==1 and res.get('quantity')!=0:
            line_obj =  self.env['sale.order.line'].browse(res.get('line_id'))
            line_obj.price_unit = tenure_rent_price

            if line_obj.inital_rental_contract_id and line_obj.inital_rental_contract_id.rental_qty != line_obj.product_uom_qty:
                line_obj.inital_rental_contract_id.rental_qty = line_obj.product_uom_qty
        return res

    @api.multi
    def _cart_find_product_line(self, product_id=None, line_id=None, **kwargs):
        # check if new line needs to be created forcefully or not
        rental_order = kwargs.get('rental_order')
        tenure_uom = int(kwargs.get('tenure_uom')) if kwargs.get('tenure_uom') else False
        tenure_value = float(kwargs.get('tenure_value')) if kwargs.get('tenure_value') else False

        if not line_id:
            flag =0
            domain = [('order_id', '=', self.id), ('product_id', '=', product_id)]
            sol_obj = self.env['sale.order.line'].sudo().search(domain)
            if sol_obj:
                for sol in sol_obj:
                    if sol.is_rental_order and rental_order:
                        if sol.rental_tenure == tenure_value and sol.rental_uom_id.id == tenure_uom:
                            return self.env['sale.order.line'].sudo().browse(sol.id)
                        else:
                            flag = 1
                    if sol.is_rental_order and not rental_order:
                        flag = 1
                    if not sol.is_rental_order and rental_order:
                        flag = 1
                    if not sol.is_rental_order and not rental_order:
                        return self.env['sale.order.line'].sudo().browse(sol.id)

            if flag==1:
                return self.env['sale.order.line']

        self.ensure_one()
        product = self.env['product.product'].browse(product_id)

        # split lines with the same product if it has untracked attributes
        if product and product.mapped('attribute_line_ids').filtered(lambda r: not r.attribute_id.create_variant) and not line_id:
            return self.env['sale.order.line']

        domain = [('order_id', '=', self.id), ('product_id', '=', product_id)]
        if line_id:
            domain += [('id', '=', line_id)]
        return self.env['sale.order.line'].sudo().search(domain)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # current_rental_tenure = fields.Float(
    #     "Tenure",
    #     readonly=True,
    #     related="current_rental_contract_id.rental_tenure",
    #     store=True,
    # )
    # current_rental_uom_id = fields.Many2one(
    #     "uom.uom",
    #     "Tenure UOM",
    #     domain=lambda self: [('is_rental_uom', '=', True)],
    #     related="current_rental_contract_id.rental_uom_id",
    #     store=True,
    # )

    @api.multi
    def _get_display_price(self, product):
        res = super(SaleOrderLine, self)._get_display_price(product)
        if self._context.get("rental_vals"):
            from_currency = self.order_id.company_id.currency_id
            price_unit = float(self._context.get("rental_vals").get("tenure_price"))
            return from_currency.compute(price_unit, self.order_id.pricelist_id.currency_id)
        return res


class RentalOrderContract(models.Model):
    _inherit = "rental.order.contract"

    rental_qty = fields.Float(
        "Quantity",
        # required=True,
        readonly=True,
        track_visibility='onchange',
        related='sale_order_line_id.product_uom_qty',
    )
