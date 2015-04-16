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
            account_ref = expense_line.get("account_ref")
            amount = expense_line.get("amount")
            memo = expense_line.get("memo")
            customer_ref = expense_line.get("customer_ref")
            expense_line_add_list.append(
                ('ExpenseLineAdd', [
                    ('AccountRef', 
                        [
                            ('ListID', account_ref.list_id),
                            ('FullName', account_ref.full_name)
                        ]
                    ),
                    ('Amount', amount),
                    ('Memo', memo),
                    ('CustomerRef', 
                        [
                            ('ListID', customer_ref.list_id),
                            ('FullName', customer_ref.full_name)
                        ]
                    )
                ])
            )


        options = [
            ('TxnDate', txn_date),
            ('DueDate', due_date),
            ('RefNumber', ref_number),
            ('Memo', memo),
            ('VendorRef', [
                ('ListID', vendor_ref.list_id),
                ('FullName', vendor_ref.full_name),
            ])
        ]

        options.extend(expense_line_add_list)

        if name == None:
            name = 'Created Vendor in %s %s quickbooks' % (first_name, last_name)
        MessageQue.objects.create(name=name, message=self.__build_xml_add_mod('Bill', 'Add', 'rq', options=options,
                                                                              request_id=ident), user=user)
        return ""



    def add_invoice(self, client, subtotal=None, discount=None, tax=None, ident=22):
        from quickbooks.models import MessageQue

        user = get_user_model().objects.get(username='quickbooks')

        options = [
            ('CustomerRef', {'ListID': '80002D16-1424209265'}),
        ]
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

        MessageQue.objects.create(name=name, message=self.__build_xml(name='Items', options=options), user=user)


    def create_query(self, name, repeat=False, active=True):
        user = get_user_model().objects.get(username='quickbooks')
        from quickbooks.models import MessageQue

        MessageQue.objects.create(name=name, message=self.__build_xml(name, request_id=3333), user=user)


    def initial(self):
        msg = []
        for name in self.names:
            msg.append({'name': name.lower(), 'message': self.__build_xml(name=name)})
        return msg

