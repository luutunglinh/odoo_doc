# -*- coding: utf-8 -*-
from odoo import models, fields,api
from odoo.exceptions import ValidationError
from datetime import timedelta

class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library Book'
    _rec_name = "short_name"
    _order = "date_release desc, name"

    name = fields.Char('Title', required=True)
    short_name = fields.Char('Short Title', required=True)
    date_release = fields.Date('Release Date')
    author_ids = fields.Many2many('res.partner', string='Authors')

    notes = fields.Text("Internal Notes")
    state =  fields.Selection(
        [('draft','Not availale'),
         ('availale', 'Available'),
         ('lost','Lost'),
         ('lost','Lost')
         ],
        'State', default = "draft"
    )
    description = fields.Html('Description', sanitize = True, strip_style = False)
    cover = fields.Binary("Book cover")
    out_of_print = fields.Boolean('Out of print')
    date_updated = fields.Datetime('Last updated', copy=False)
    pages = fields.Integer('Number of pages', groups = 'base.group_user', states = {'lost':[('readonly',True)]}
                           ,help = "Total book page cout", company_dependent = False
                           )
    #states = {'lost':[('readonly',True)]} onchange trường lost trong selection thành chỉ đọc
    reader_rating = fields.Float(
        'Reader Average Rating',
        digits=(14, 4),  # Optional precision (total, decimals),
    )
    cost_price = fields.Float('Book Cost', digits='Book Price')
    currency_id = fields.Many2one('res.currency',string ="Currency")
    retail_price = fields.Monetary('Retail Price')

    publisher_id = fields.Many2one('res.partner', string='Publisher',
                                   # optional:
                                   ondelete='set null',
                                   context={},
                                   domain=[],
                                   )

    publisher_city = fields.Char('Publisher City', related='publisher_id.city', readonly=True)
    # hiện tên thành phố theo user
    age_days = fields.Float(
        string="Day Since Release",
        compute = '_compute_age',
        inverse = '_inverse_age',
        search = '_search_age',
        store = False, #sắp xếp các trường trong database, sau khi computed, true thì dễ dàng tím kiếm k cần phải dùng hàm search
        compute_sudo = True,
    )
    def name_get(self):
        """ This method used to customize display name of the record """
        result = []
        for rec in self:
            rec_name = "%s (%s)" %(rec.name, rec.date_release)
            result.append((rec.id,rec_name))
        return result

    class ResPartner(models.Model):
        _inherit = "res.partner"

        published_book_ids = fields.One2many('library.book','publisher_id',string="Publised Book")
        authored_book_ids = fields.Many2many('library.book', string="Authored Books")


    _sql_constraints = [
        ('name_uniq','UNIQUE (name)', 'Book title must be unique'),
        ('positive_page', 'CHECK(pages > 0)', 'No of pages must be positive'),
    ]

    @api.constrains('date_release')
    def check_release_date(self):
        for rec in self:
            if rec.date_release and rec.date_release > fields.Date.today():
                raise models.ValidationError('Release date must be in the past')

    @api.depends('date_release')
    def _compute_age(self):
        print('ok')
        today = fields.Date.today()
        for book in self:
            if book.date_release:
                delta = today - book.date_release
                book.age_days = delta.days
            else:
                book.age_days = 0

    def _inverse_age(self):
        today = fields.Date.today()
        for book in self.filtered('date_release'):
            d = today - timedelta(days=book.age_days)
            book.date_release = d
            print('ok2',d)

    def _search_age(self, operator, value):
        print('ok3',value)
        today = fields.Date.today()
        value_days = timedelta(days=value)
        value_date = today - value_days
        # convert the operator:
        # book with age > value have a date < value_date
        operator_map = {
            '>': '<', '>=': '<=',
            '<': '>', '<=': '>=',
        }
        new_op = operator_map.get(operator, operator)
        return [('date_release', new_op, value_date)]