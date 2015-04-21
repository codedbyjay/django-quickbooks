from django.contrib.auth import get_user_model
from quickbooks.qwc_xml import qrequest
from quickbooks.uttils import xml_soap
import xmltodict
import logging
from collections import OrderedDict

class QBXML:
    def __init__(self):
        self.xml_prefix = '''<?xml version="1.0" encoding="utf-8"?><?qbxml version="2.1"?>'''
        self.names = [
            'Customer',
            'Bill',
            'Account',
            'Check',
            'Account',
            'Estimate',
            'Invoice',
            'ReceivePayment',
            'Vendor',
            'ToDo',
            'Item',
            'SalesReceipt',
        ]

        self.method = [
            'Query',
            'Add',
            'Mod',
        ]

    def __build_name(self, name='Customer', method='Query', request='Rq'):
        """ Builds the name of the query
        :param name:
        :param method:
        :param request:
        :return:
        """
        method = method.title()
        request = request.title()
        name = name.title()
        return name + method + request

    def __build_rq_name(self, name, method):
        return name.title() + method.title()


    def __build__json(self, name, method='query', request='rq', request_id=None):
        request_id = '22222'
        c = {
            'QBXML': {
                'QBXMLMsgsRq': {
                    '@onError': 'stopOnError',
                    self.__build_name(name, method=method, request=request): {
                        '@requestID': request_id,
                        # 'FromModifiedDate' : "2014-11-30"
                    }
                }
            }
        }

        return c

    def __build_xml(self, name, method='query', request='rq', request_id=None, options={}):
        request_id = '22222'
        internal_options = {'@requestID': request_id, }
        internal_options.update(options)
        c = {
            'QBXML': {
                'QBXMLMsgsRq': {
                    '@onError': 'stopOnError',

                    self.__build_name(name, ):
                        internal_options
                }
            }
        }
        return self.xml_prefix + xmltodict.unparse(c, full_document=False)

    def __build_xml_add_mod(self, name, method='query', request='rq', request_id=3232, options=None):

        c = {
            'QBXML': {
                'QBXMLMsgsRq': {
                    '@onError': 'stopOnError',
                    self.__build_name(name, method=method, request=request): {
                        '@requestID': str(request_id),
                        str(name).title() + str(method).title():
                            OrderedDict(options)

                    }
                }
            }
        }
        return self.xml_prefix + xmltodict.unparse(c, full_document=False)

    def invoice(self):
        return ""

    def add_customer(self, name=None, first_name=None, last_name=None, ident=0):
        from quickbooks.models import MessageQue

        user = get_user_model().objects.get(username='quickbooks')

        options = [
            ('Name', "%s, %s" % (last_name, first_name)),
            ('FirstName', first_name),
            ('LastName', last_name),
        ]

        if name == None:
            name = 'Created Customer in %s %s quickbooks' % (first_name, last_name)
        MessageQue.objects.create(name=name, message=self.__build_xml_add_mod('Customer', 'Add', 'rq', options=options,
                                                                              request_id=ident), user=user)
        return ""

    def edit_customer(self, list_id, first_name=None, last_name=None, ident=0, edit_sequence=0):
        from quickbooks.models import MessageQue

        user = get_user_model().objects.get(username='quickbooks')

        options = [
            ('ListID', list_id),
            ('EditSequence', edit_sequence),
            ('Name', "%s, %s" % (last_name, first_name)),
            ('FirstName', first_name),
            ('LastName', last_name),
        ]
        name = 'Edited Customer in %s %s quickbooks' % (first_name, last_name)
        MessageQue.objects.create(name=name, message=self.__build_xml_add_mod('Customer', 'Mod', 'rq', options=options,
                                                                              request_id=ident), user=user)

    def add_vendor(self, name=None, first_name=None, last_name=None, company_name=None, ident=0):
        from quickbooks.models import MessageQue

        user = get_user_model().objects.get(username='quickbooks')

        options = [
            ('Name', "%s, %s" % (last_name, first_name)),
            ('CompanyName', company_name),
            ('FirstName', first_name),
            ('LastName', last_name),
        ]

        if name == None:
            name = 'Created Vendor in %s %s quickbooks' % (first_name, last_name)
        MessageQue.objects.create(name=name, message=self.__build_xml_add_mod('Vendor', 'Add', 'rq', options=options,
                                                                              request_id=ident), user=user)
        return ""

    def add_bill(self, vendor_ref, txn_date=None, due_date=None, ref_number=None, memo=None, 
            expense_line_add=[], ident=0):

        from quickbooks.models import MessageQue

        user = get_user_model().objects.get(username='quickbooks')

        expense_line_add_list = []
        for expense_line in expense_line_add:
            account_ref = expense_line.get("account_ref", None)
            amount = expense_line.get("amount", "")
            memo = expense_line.get("memo", "")
            customer_ref = expense_line.get("customer_ref", None)
            ordered_dict = OrderedDict()
            if account_ref:
                ordered_dict['AccountRef'] = OrderedDict([
                        ("ListID", account_ref.list_id),
                        ("FullName", account_ref.full_name)
                    ])
            ordered_dict['Amount'] = amount
            ordered_dict['Memo'] = memo
            if customer_ref:
                ordered_dict['CustomerRef'] = OrderedDict([
                        ("ListID", customer_ref.list_id),
                        ("FullName", customer_ref.full_name)
                    ])
            expense_line_add_list.append(ordered_dict)

        item_line_add_list = []
        for item_line in item_line_add:
            sales_rep_ref = item_line.get("sales_rep_ref", None)
            customer_ref = item_line.get("customer_ref", None)
            item_ref = item_line.get("item_ref", None)
            serial_number = item_line.get("serial_number", "")
            lot_number = item_line.get("lot_number", "")
            desc = item_line.get("desc", "")
            quantity = item_line.get("quantity")
            amount = item_line.get("amount")
            cost = item_line.get("cost")
            unit_of_measure = item_line.get("unit_of_measure", "")
            memo = item_line.get("memo", "")
            ordered_dict = OrderedDict()
            if item_ref:
                ordered_dict["ItemRef"] = OrderedDict([
                        ("ListID", item_ref.list_id),
                        ("FullName", item_ref.full_name)
                    ])
            if serial_number:
                ordered_dict["SerialNumber"] = serial_number
            elif lot_number:
                ordered_dict["LotNumber"] = lot_number
            ordered_dict["Desc"] = desc
            ordered_dict["Quantity"] = quantity
            ordered_dict["UnitOfMeasure"] = unit_of_measure
            ordered_dict["Cost"] = cost
            ordered_dict["Amount"] = amount
            if customer_ref:
                ordered_dict["CustomerRef"] = OrderedDict([
                        ("ListID", customer_ref.list_id),
                        ("FullName", customer_ref.full_name)
                    ])
            if sales_rep_ref:
                ordered_dict["SalesRepRef"] = OrderedDict([
                        ("ListID", sales_rep_ref.list_id),
                        ("FullName", sales_rep_ref.full_name)
                    ])
            item_line_add_list.append(ordered_dict)

        options = [
            ('VendorRef',   
                OrderedDict([
                    ('ListID', vendor_ref.list_id),
                    ('FullName', vendor_ref.full_name),
                ])
            ),
            ('TxnDate' , txn_date),
            ('DueDate', due_date),
            ('RefNumber', ref_number),
            ('Memo', memo),
        ]

        if expense_line_add_list:
            options.append(('ExpenseLineAdd', expense_line_add_list))
        elif item_line_add_list:
            options.append(('ItemLineAdd', item_line_add_list))

        name = 'Created Bill in quickbooks'
        MessageQue.objects.create(name=name, message=self.__build_xml_add_mod('Bill', 'Add', 'rq', options=options,
                                                                              request_id=ident), user=user)
        return ""



    def add_invoice(self, client=None, memo=None, ref_number=None, items=[], ident=22):
        from quickbooks.models import MessageQue

        user = get_user_model().objects.get(username='quickbooks')

        options = []
        if client:
            options.append(
                ('CustomerRef', OrderedDict(
                    [
                        ('ListID', client.list_id),
                        ('FullName', client.full_name)
                    ]
                ))
            )
        options.append(('RefNumber', ref_number,))
        options.append(('Memo', memo,))
        line_items = []
        for (item, qty, total) in items:
            line_items.append(OrderedDict([
                ("Desc", item),
                ("Quantity", qty),
                ("Amount", total)
            ]))
        options.append(('InvoiceLineAdd', line_items))
        MessageQue.objects.create(name='Invoice created',
                                  message=self.__build_xml_add_mod('Invoice', 'Add', 'rq', options=options,
                                                                   request_id=ident), user=user)

    def get_customers(self, date_from=None):
        """
        :param date_from: need to be a date in format "2014-06-05"
        :return:
        """
        # This will get all customers FIXME: add FROM option
        from quickbooks.models import MessageQue

        user = get_user_model().objects.get(username='quickbooks')
        name = 'Get All Customers'
        options = {}
        if date_from:
            options.update({'FromModifiedDate': date_from})

        MessageQue.objects.create(name=name, message=self.__build_xml(name='Customer', options=options), user=user)

    def get_accounts(self, date_from=None):
        """
        :param date_from: need to be a date in format "2014-06-05"
        :return:
        """
        # This will get all customers FIXME: add FROM option
        from quickbooks.models import MessageQue

        user = get_user_model().objects.get(username='quickbooks')
        name = 'Get All Accounts'
        options = {}
        if date_from:
            options.update({'FromModifiedDate': date_from})

        MessageQue.objects.create(name=name, message=self.__build_xml(name='Account', options=options), user=user)



    def get_invoices(self, date_from=None):
        """
        :param date_from: need to be a date in format "2014-06-05"
        :return:
        """
        # This will get all customers FIXME: add FROM option
        from quickbooks.models import MessageQue

        user = get_user_model().objects.get(username='quickbooks')
        name = 'Get All Customers'
        options = {}
        if date_from:
            options.update({'FromModifiedDate': date_from})

        MessageQue.objects.create(name=name, message=self.__build_xml(name='Customer', options=options), user=user)

    def get_vendors(self, date_from=None):
        """
        :param date_from: need to be a date in format "2014-06-05"
        :return:
        """
        # This will get all customers FIXME: add FROM option
        from quickbooks.models import MessageQue

        user = get_user_model().objects.get(username='quickbooks')
        name = 'Get All Vendors'
        options = {}
        if date_from:
            options.update({'FromModifiedDate': date_from})

        MessageQue.objects.create(name=name, message=self.__build_xml(name='Vendor', options=options), user=user)


    def get_bills(self, date_from=None):
        """
        :param date_from: need to be a date in format "2014-06-05"
        :return:
        """
        # This will get all customers FIXME: add FROM option
        from quickbooks.models import MessageQue

        user = get_user_model().objects.get(username='quickbooks')
        name = 'Get All Bills'
        options = {}
        if date_from:
            options.update({'FromModifiedDate': date_from})

        MessageQue.objects.create(name=name, message=self.__build_xml(name='Bill', options=options), user=user)



    def get_items(self, date_from=None):
        """
        :param date_from: need to be a date in format "2014-06-05"
        :return:
        """
        # This will get all customers FIXME: add FROM option
        from quickbooks.models import MessageQue

        user = get_user_model().objects.get(username='quickbooks')
        name = 'Get All Items'
        options = {}
        if date_from:
            options.update({'FromModifiedDate': date_from})

        MessageQue.objects.create(name=name, message=self.__build_xml(name='Item', options=options), user=user)


    def create_query(self, name, repeat=False, active=True):
        user = get_user_model().objects.get(username='quickbooks')
        from quickbooks.models import MessageQue

        MessageQue.objects.create(name=name, message=self.__build_xml(name, request_id=3333), user=user)


    def initial(self):
        msg = []
        for name in self.names:
            msg.append({'name': name.lower(), 'message': self.__build_xml(name=name)})
        return msg

