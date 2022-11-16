# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
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
{
  "name"                 :  "Odoo Rental Sale",
  "summary"              :  "Odoo Rental Sale Management allows you to make a product available for rent and offer the same to the people.",
  "category"             :  "Sales",
  "version"              :  "1.0.1",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Rental-Sale.html",
  "description"          :  """Odoo Rental Sale Management
Rental Sale Management
Rent
Odoo Rental Sale Management in Odoo
Rental Products
Rent Products
Rental Management
Odoo Website Rental Sale
Odoo Marketplace Rental Sale
Rent Product Tenure
Hire Products
Hiring Management""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=odoo_sale_rental",
  "depends"              :  [
                             'sale_stock',
                             'sale_management',
                            ],
  "data"                 :  [
                             'security/rental_sale_security.xml',
                             'security/ir.model.access.csv',
                             'data/uom_uom_rental_data.xml',
                             'data/rental_reason_data.xml',
                             'data/product_demo.xml',
                             'data/rental_cron.xml',
                             'data/ir_sequence_data.xml',
                             'wizard/rental_order_transient_view.xml',
                             'wizard/renew_rental_order_transient_view.xml',
                             'wizard/rental_reason_transient_view.xml',
                             'views/rental_product_view.xml',
                             'views/rental_view.xml',
                             'views/rental_order_view.xml',
                             'views/rental_menu_view.xml',
                             'views/inherited_sale_order_views.xml',
                             'views/inherit_picking_view.xml',
                             'views/res_config_settings_views.xml',
                             'views/rental_contract_report_template.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  99,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}