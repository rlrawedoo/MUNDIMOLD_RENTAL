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

from odoo import http,fields
from odoo.http import request
from datetime import datetime, date
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_sale.controllers.main import TableCompute, QueryURL, WebsiteSale
from odoo.tools.misc import flatten
import logging
import json
_logger = logging.getLogger(__name__)

PPG = 12  # Products Per Page
PPR = 4   # Products Per Row
try:
    import urlparse
    from urllib import urlencode
except: # For Python 3
    import urllib.parse as urlparse
    from urllib.parse import urlencode

class WebsiteRentalSale(http.Controller):

    @http.route(["/set/tenure/maxvalue"], type="json", auth="public", website=True)
    def _set_tenure_maxvalue(self, product_id, tenure_uom_id):
        product_id = request.env['product.product'].sudo().browse(product_id)
        max_tenure_value = product_id.get_tenure_maxvalue(int(tenure_uom_id))
        return {"max_value": max_tenure_value,}

    @http.route(["/get/tenure/price"], type="json", auth="public", website=True)
    def _get_tenure_price(self, product_id, tenure_uom_id=None, tenure_value=None, tenure_id=None):
        if tenure_id:
            rent_price = request.env['product.rental.tenure'].browse(int(tenure_id)).rent_price
            return str('%.2f' % rent_price)
        tenure_uom_id = request.env['uom.uom'].sudo().browse(tenure_uom_id).id or False
        product_id = request.env['product.product'].sudo().browse(product_id)
        max_tenure_value = product_id.get_tenure_maxvalue(int(tenure_uom_id))
        if float(tenure_value) > max_tenure_value:
            return {"error": "true", "max_value": max_tenure_value,}
        if tenure_uom_id and tenure_value and product_id:
            tenure_price = product_id.get_product_tenure_price(float(tenure_value), tenure_uom_id)
            return {"error": "false","tenure_price":str('%.2f' % round(tenure_price[1], 2)),} if tenure_price else {}

    @http.route(['/rental/order/renew'], type='http', auth='public', website=True,)
    def renew_rental_order(self, **kw):
        url = request.httprequest.referrer
        params = {}
        try:
            product_id = request.env['product.product'].browse(int(kw.get('product_id')))
            rental_order = kw.get('is_rental_product', None) and product_id.rental_ok
            sale_order_line_id = request.env['sale.order.line'].browse(int(kw.get("sale_order_line_id")))
            if rental_order:
                tenure_uom = False
                tenure_value = 0
                tenure_price = 0
                if kw.get('standard') and kw.get('tenure_id'):
                    tenure_id = request.env['product.rental.tenure'].browse(int(kw.get('tenure_id')) if kw.get('tenure_id') else False)
                    tenure_uom = tenure_id.rental_uom_id.id if tenure_id else False
                    tenure_value = float(tenure_id.tenure_value) if tenure_id else 0
                    tenure_price = float(tenure_id.rent_price) if tenure_id else 0

                if kw.get('custom') and kw.get('custom_tenure_price'):
                    tenure_uom = request.env['uom.uom'].sudo().browse(kw.get('tenure_uom')).id or False
                    tenure_value = float(kw.get('tenure_value')) or 0
                    tenure_price = float(product_id.get_product_tenure_price(tenure_value, tenure_uom) or kw.get('custom_tenure_price') or 0)

                    return_value_price_pair = product_id.get_product_tenure_price(tenure_value, tenure_uom)
                    if return_value_price_pair:
                        tenure_value = return_value_price_pair[0]
                        tenure_price = return_value_price_pair[1]
                taxes_ids = []
                if product_id.taxes_id:
                    taxes_ids = product_id.taxes_id.ids
                ro_contract_values = {
                    'sale_order_line_id': sale_order_line_id.id,
                    'product_rental_agreement_id': product_id.rental_agreement_id.id,
                    'price_unit': sale_order_line_id.product_id.currency_id.compute(tenure_price, sale_order_line_id.order_id.pricelist_id.currency_id),
                    'rental_qty': sale_order_line_id.product_uom_qty,
                    'rental_uom_id': tenure_uom,
                    'rental_tenure': tenure_value,
                    'tax_ids': [(6, 0, taxes_ids)],
                    'is_renewal_contract': True,
                }
                new_created_rental_contract = request.env['rental.order.contract'].sudo().create(ro_contract_values)
                new_created_rental_contract.action_confirm()
                new_created_rental_contract = new_created_rental_contract.sudo()
                inv = new_created_rental_contract.create_rental_invoice()
                inv_id = inv.get("res_id") or False
                if inv_id:
                    inv_obj = request.env['account.invoice'].browse(int(inv_id))
                    inv_obj.sudo().action_invoice_open()
                    params = {'renew_success': inv_obj.id}
                if new_created_rental_contract and len(sale_order_line_id.rental_contract_ids) == 1:
                    sale_order_line_id.inital_rental_contract_id = new_created_rental_contract.id
                else:
                    contract_to_check = False
                    if sale_order_line_id.current_rental_contract_id:
                        contract_to_check = sale_order_line_id.current_rental_contract_id
                    else:
                        contract_to_check = sale_order_line_id.inital_rental_contract_id
                    if contract_to_check and not (contract_to_check.check_product_received()):
                        #code to link current contract done move to latest contrcat
                        new_created_rental_contract.link_move_to_new_contract(
                            contract_to_check, new_created_rental_contract)
                        new_created_rental_contract.start_time = fields.datetime.now()
                        sale_order_line_id.current_start_time = new_created_rental_contract.start_time
                    sale_order_line_id.write({
                        "current_rental_contract_id": new_created_rental_contract.id,
                        "last_renewal_time": datetime.now(),
                    })
                    new_created_rental_contract.sale_order_line_id.write(
                        {"rental_state": "in_progress"})
        except Exception as e:
            params = {'renew_error': 1}
            _logger.info("-------------Exception: %r ------------------", e)
            pass
        url_parts = list(urlparse.urlparse(url))
        query = dict(urlparse.parse_qsl(url_parts[4]))
        if query.get("renew_success") or query.get("renew_error"):
            pass
        else:
            query.update(params)
        url_parts[4] = urlencode(query)
        url = urlparse.urlunparse(url_parts)
        return request.redirect(url)

class WebsiteSale(WebsiteSale):

    def _get_rental_search_domain(self, search, rental_categ, category, attrib_values):
        # domain = request.website.sale_product_domain() #gives [('sale_ok','=',True)]
        domain= []
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                    ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]
        domain += [('rental_ok', '=', True)]

        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]

        if rental_categ:
            domain += [('rental_categ_id','=', int(rental_categ))]

        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]

        return domain

    def get_parent_categs(self, categ, categ_list=[]):
        if categ.parent_id:
            categ_list.append(categ.parent_id.id)
            self.get_parent_categs(categ=categ.parent_id, categ_list=categ_list)
        return request.env["product.public.category"].browse(categ_list)

    @http.route([
        '/shop/rental',
        '/shop/rental/page/<int:page>',
        '/shop/rental/category/<model("product.public.category"):category>',
        '/shop/rental/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop_rental(self, rental_categ=0, page=0, category=None, search='', ppg=False, **post):
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}
        domain = self._get_rental_search_domain(search, rental_categ, category, attrib_values)

        keep = QueryURL('/shop/rental', rental_categ=rental_categ, category=category and int(category), search=search, attrib=attrib_list, order=post.get('order'))

        compute_currency, pricelist_context, pricelist = self._get_compute_currency_and_context()

        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = "/shop/rental"
        if search:
            post["search"] = search
        if category:
            category = request.env['product.public.category'].browse(int(category))
            url = "/shop/rental/category/%s" % slug(category)
        if rental_categ:
            rental_categ = request.env['rental.product.category'].browse(int(rental_categ))
            post["rental_categ"] = rental_categ
        if attrib_list:
            post['attrib'] = attrib_list

        categs = request.env['product.public.category'].search([('parent_id', '=', False)])
        rental_categs = request.env['rental.product.category'].search([('hide_all_product','=',False)])


        Product = request.env['product.template']

        parent_category_ids = []
        if category:
            parent_category_ids = [category.id]
            current_category = category
            while current_category.parent_id:
                parent_category_ids.append(current_category.parent_id.id)
                current_category = current_category.parent_id

        product_count = Product.search_count(domain)
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        products = Product.search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))

        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            selected_products = Product.search(domain, limit=False)
            attributes = ProductAttribute.search([('attribute_line_ids.product_tmpl_id', 'in', selected_products.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        # to apply domain in category of rental shop according to product categories added in rental category
        if rental_categ:
            categ_domain = []
            for c in rental_categ.public_categ_ids:
                categ_domain.append(self.get_parent_categs(c, []).ids)
            categ_domain.append(rental_categ.public_categ_ids.ids)
            categ_domain = flatten(categ_domain)

        values = {
            'search': search,
            'category': category,
            'rental_categ':rental_categ,
            'categ_domain':categ_domain if rental_categ else False,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg),
            'rows': PPR,
            'categories': categs,
            'rental_categs':rental_categs,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            'parent_category_ids': parent_category_ids,
            'is_rental_page': True,
        }
        if category:
            values['main_object'] = category
        return request.render("website_sale.products", values)

    @http.route(['/shop/rental/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product_rental(self, product, rental_categ=0, category='', search='', **kwargs):
        product_context = dict(request.env.context,
                               active_id=product.id,
                               partner=request.env.user.partner_id)
        ProductCategory = request.env['product.public.category']
        RentalCategory = request.env['rental.product.category']

        if category:
            category = ProductCategory.browse(int(category)).exists()

        if rental_categ:
            rental_categ = RentalCategory.browse(int(rental_categ))

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attrib_set = {v[1] for v in attrib_values}

        keep = QueryURL('/shop/rental', rental_categ=rental_categ, category=category and category.id, search=search, attrib=attrib_list)

        categs = ProductCategory.search([('parent_id', '=', False)])

        pricelist = request.website.get_current_pricelist()

        from_currency = request.env.user.company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: from_currency.compute(price, to_currency)

        if not product_context.get('pricelist'):
            product_context['pricelist'] = pricelist.id
            product = product.with_context(product_context)

        values = {
            'search': search,
            'category': category,
            'rental_categ':rental_categ,
            'pricelist': pricelist,
            'attrib_values': attrib_values,
            'compute_currency': compute_currency,
            'attrib_set': attrib_set,
            'keep': keep,
            'categories': categs,
            'main_object': product,
            'product': product,
            'get_attribute_exclusions': self._get_attribute_exclusions,
            'is_rental_product':True,
        }
        return request.render("website_sale.product", values)

    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        product_id = request.env['product.product'].browse(int(product_id))
        rental_order = kw.get('is_rental_product', None) and product_id.rental_ok
        if rental_order:
            try:
                tenure_uom = False
                tenure_value = 0
                tenure_price = 0
                if not kw.get('standard') and not kw.get('custom'):
                    return request.redirect("/shop/cart")
                if kw.get('standard') and kw.get('tenure_id'):
                    tenure_id = request.env['product.rental.tenure'].browse(int(kw.get('tenure_id')) if kw.get('tenure_id') else False)
                    tenure_uom = tenure_id.rental_uom_id.id if tenure_id else False
                    tenure_value = float(tenure_id.tenure_value) if tenure_id else 0
                    tenure_price = float(tenure_id.rent_price) if tenure_id else 0
                if kw.get('custom') and kw.get('custom_tenure_price') :
                    tenure_uom = request.env['uom.uom'].sudo().browse(kw.get('tenure_uom')).id or False
                    tenure_value = float(kw.get('tenure_value')) or 0
                    tenure_price = float(product_id.get_product_tenure_price(tenure_value, tenure_uom) or kw.get('custom_tenure_price') or 0)
                    return_value_price_pair = product_id.get_product_tenure_price(tenure_value, tenure_uom)
                    if return_value_price_pair:
                        tenure_value = return_value_price_pair[0]
                        tenure_price = return_value_price_pair[1]
                so = request.website.sale_get_order(force_create=1)
                if so.state != 'draft':
                    request.session['sale_order_id'] = None
                    so = request.website.sale_get_order(force_create=True)
                rental_vals = {
                    'tenure_uom' : tenure_uom,
                    'tenure_value' : tenure_value,
                    'tenure_price' : tenure_price,
                }
                product_custom_attribute_values = None
                if kw.get('product_custom_attribute_values'):
                    product_custom_attribute_values = json.loads(kw.get('product_custom_attribute_values'))
                no_variant_attribute_values = None
                if kw.get('no_variant_attribute_values'):
                    no_variant_attribute_values = json.loads(kw.get('no_variant_attribute_values'))
                line = so.with_context(rental_vals=rental_vals)._cart_update(
                    product_id=int(product_id),
                    add_qty=float(add_qty),
                    set_qty=float(set_qty),
                    product_custom_attribute_values=product_custom_attribute_values,
                    no_variant_attribute_values=no_variant_attribute_values,
                    rental_order = True,
                    tenure_uom = tenure_uom,
                    tenure_value = tenure_value,
                )
                return request.redirect("/shop/cart")
            except:
                return request.redirect("/shop/cart")
        res = super(WebsiteSale, self).cart_update(product_id, add_qty, set_qty, **kw)
        return res
