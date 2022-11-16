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
  "name"                 :  "Odoo Website Rental Sale",
  "summary"              :  "Set up rental products on your Odoo website. The module provides an easy way to manage and rent out products to customer in Odoo",
  "category"             :  "Website",
  "version"              :  "1.3.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Website-Rental-Sale.html",
  "description"          :  """Create rental products in Odoo
Publish rental products
Manage rental product in Odoo
Renting business
Manage rent on items
Rent items
Rent products
Odoo Website Rental Sale
Rental Sale in Odoo Website
Odoo Lease Management
Odoo Website Lease Sale
Odoo Rental Sale
Odoo Website Rental Management
Rental Management in Odoo Website
Odoo Odoo Website Rental Sale
Rental service in Odoo
Manage rental products in Odoo""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=odoo_website_sale_rental&lifetime=60&lout=0&custom_url=/shop/rental",
  "depends"              :  [
                             'account_payment',
                             'website_sale',
                             'odoo_sale_rental',
                            ],
  "data"                 :  [
                             'security/ir.model.access.csv',
                             'security/access_control_security.xml',
                             'views/templates.xml',
                             'views/rental_product_view.xml',
                             'views/inherit_website_template.xml',
                             'views/inherit_website_cart_template.xml',
                             'views/my_account_rental_contract_template.xml',
                             'data/rental_data.xml',
                            ],
  "demo"                 :  [],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  100,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}
