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

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class RentalProductTemplate(models.Model):
    _inherit = 'product.template'

    rental_tenure_id = fields.Many2one(
        "product.rental.tenure",
        "Rental Tenure Starting",
    )

    @api.multi
    def toggle_website_published(self):
        for record in self:
            if not record.website_published and not record.tenure_type_standard and not record.tenure_type_custom:
                raise UserError(_("Please select tenure type standard/custom to publish this product."))
            if not record.website_published and not record.rental_tenure_ids:
                raise UserError(_("Please add atleast one Rental Tenure to publish this product."))
            if not record.website_published and not record.rental_tenure_id:
                raise UserError(_("Please select starting rental tenure to show in website."))
            record.sudo().website_published = not record.sudo().website_published

    @api.multi
    def get_tenure_maxvalue(self, tenure_uom_id):
        tenure_uom_id = self.env['uom.uom'].sudo().browse(tenure_uom_id) or False
        if self.rental_ok and tenure_uom_id:
            max_tenure_value = max(self.rental_tenure_ids.filtered(lambda t: t.rental_uom_id.id == tenure_uom_id.id).mapped(lambda l : l.max_tenure_value))
            return max_tenure_value

    @api.multi
    @api.onchange("rental_tenure_ids")
    def _validate_rental_starting_tenure(self):
        for rec in self:
            if rec.rental_ok and rec.rental_tenure_id and rec.rental_tenure_id.is_default == False:
                raise UserError("Please select starting rental tenure which is default tenure.")
        return

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def get_tenure_maxvalue(self, tenure_uom_id):
        self.ensure_one()
        return self.product_tmpl_id.get_tenure_maxvalue(tenure_uom_id)

class ProductRentalTenure(models.Model):
    _inherit = 'product.rental.tenure'
    _order = "sequence desc"

    sequence = fields.Integer('sequence', help="Sequence to display tenures in webiste")


class RentalProductCategory(models.Model):
    _inherit = 'rental.product.category'

    public_categ_ids = fields.Many2many(
        "product.public.category",
        "rental_product_categ_rel",
        "rental_categ_id",
        "public_categ_id",
        string="eCommerce Categories",
        help="Product Categories for this rental category to be shown in website in the"
        " Rental Shop page (online catalog grid) to help "
        "customers find all the items within a category. A product can belong to several categories."
    )
