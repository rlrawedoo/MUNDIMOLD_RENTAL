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

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import consteq
import logging
_logger = logging.getLogger(__name__)

class PortalAccount(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(PortalAccount, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        my_rental_orders_count = request.env['sale.order.line'].search_count([
            ('order_partner_id', '=', partner.id),('is_rental_order','=',True),('state','!=','draft'),
        ])
        values['my_rental_orders_count'] = my_rental_orders_count
        return values

    # ------------------------------------------------------------
    # My Rental Orders
    # ------------------------------------------------------------

    def _rental_orders_check_access(self, rental_order_id, access_token=None):
        rental_orders = request.env['sale.order.line'].browse([rental_order_id])
        rental_orders_sudo = rental_orders.sudo()
        try:
            rental_orders.check_access_rights('read')
            rental_orders.check_access_rule('read')
        except AccessError:
            if not access_token or not consteq(rental_orders_sudo.access_token, access_token):
                raise
        return rental_orders_sudo

    def _rental_orders_get_page_view_values(self, rental_orders, access_token, **kwargs):
        values = {
            'page_name': 'rental_order',
            'rental_orders': rental_orders,
        }
        if access_token:
            values['no_breadcrumbs'] = True
        if kwargs.get('error'):
            values['error'] = kwargs['error']
        if kwargs.get('warning'):
            values['warning'] = kwargs['warning']
        if kwargs.get('success'):
            values['success'] = kwargs['success']

        history = request.session.get('my_rental_orders_history', [])
        values.update(get_records_pager(history, rental_orders))
        values.update(request.env['payment.acquirer']._get_available_payment_input(rental_orders.order_partner_id, rental_orders.order_partner_id.company_id))
        return values

    @http.route(['/my/rental/orders', '/my/rental/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_rental_orders(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        RentalOrdersObj = request.env['sale.order.line']

        domain = [
            ('order_partner_id', '=', partner.id),('is_rental_order','=',True),('state','!=','draft'),
        ]

        searchbar_sortings = {
            'create_date': {'label': _('Create Date'), 'order': 'create_date asc'},
            'start_time': {'label': _('Start Time'), 'order': 'current_start_time asc'},
            'end_time': {'label': _('End Time'), 'order': 'current_end_time asc'},
            'name': {'label': _('Rental Order Id'), 'order': 'rental_sequence asc'},
        }
        # default sort by order
        if not sortby:
            sortby = 'create_date'
        order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('sale.order.line', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        rental_order_count = RentalOrdersObj.search_count(domain)

        # make pager
        pager = request.website.pager(
            url="/my/rental/orders",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=rental_order_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        rental_orders = RentalOrdersObj.search(domain, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_rental_orders_history'] = rental_orders.ids[:100]

        values.update({
            'date': date_begin,
            'rental_orders_obj': rental_orders.sudo(),
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/rental/orders',
            'page_name': 'rental_order',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("odoo_website_sale_rental.portal_my_rental_orders", values)


    @http.route(['/my/rental/orders/<int:rental_order_id>'], type='http', auth="user", website=True)
    def portal_my_rental_order_detail(self, rental_order_id=None, access_token=None, **kw):
        line_check = request.env['sale.order.line'].browse([rental_order_id])
        if not line_check.exists():
            return request.render('website.404')
        try:
            rental_order_sudo = self._rental_orders_check_access(rental_order_id, access_token)
        except AccessError:
            return request.redirect('/my')
        values = self._rental_orders_get_page_view_values(rental_order_sudo, access_token, **kw)
        if kw.get('renew_success'):
            values.update({
                'renew_success' : kw.get('renew_success'),
            })
        else:
            values.update({
                'renew_error' : kw.get('renew_error'),
            })
        return request.render("odoo_website_sale_rental.portal_my_rental_order_page", values)
