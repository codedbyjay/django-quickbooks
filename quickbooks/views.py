import os
import logging as log

from django.db.models import get_app, get_models
from django.shortcuts import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate

from lxml import etree

from quickbooks.models import QWCTicket
from quickbooks.models import UserProfile
from quickbooks.models import ReceiveResponse
from quickbooks.models import MessageQue

from quickbooks.qwc_xml import authenticated
from quickbooks.qwc_xml import failed
from quickbooks.qwc_xml import close_connection
from quickbooks.qwc_xml import processed
from quickbooks.qwc_xml import process_failed
from quickbooks.qwc_xml import qrequest

from quickbooks.uttils import convert
from quickbooks.uttils import xml_soap
from quickbooks.uttils import generate_qbc_file
from quickbooks.uttils import tag

from quickbooks.qbxml import QBXML

logging = log.getLogger(__name__)


@csrf_exempt
def show_wsdl(request):
    contents = ""
    with(open(os.path.join(settings.BASE_DIR, 'quickbooks', 'qb.wsdl'), 'r')) as f:
        contents = f.read()
    return HttpResponse(contents, content_type='text/xml')


@csrf_exempt
def home(request):
    c = request.body
    # logging.debug(c)
    if request.method == "GET":
        logging.debug("kdhohdjdhdj")
        return HttpResponse('The request need to be POST')
    url = 'file://' + os.path.join(settings.BASE_DIR, 'quickbooks', 'qb.wsdl')

    # FIXME: huge_tree allow this thing to eat up your memory!
    parser = etree.XMLParser(huge_tree=True)
    contents = etree.parse(request, parser)
    root = contents.getroot()

    # We need to listen to authenticate, token or error.
    cont = root[0][0]
    ticket = cont.find(tag('ticket'))
    if cont.tag == tag('authenticate', 'intuit'):
        logging.debug('Authentication call detected')
        username = cont.find(tag('strUserName')).text
        password = cont.find(tag('strPassword')).text

        # Authenticate with database
        a = authenticate(username=username, password=password)
        if a:
            logging.debug('Valid Authentication username and password user: %s' % (a.username))
            # everything active need to be inactive
            ac = QWCTicket.objects.filter(user=a, active=True)
            if ac != None:
                for ca in ac:
                    ca.active = False
                    ca.save()
            ti = QWCTicket.objects.create(user=a)
            logging.debug('Ticket has been created ticket: %s' % (ti.ticket))
            # resp = client.service.authenticateResponse(ti.ticket).envelope
            s = ''
            try:
                s = a.userprofile.company_file
                logging.debug('company file detected: %s' % (s))
            except:
                logging.debug('Company file not found')
            logging.debug("Authenticated xml message sent")
            return HttpResponse(authenticated % (ti.ticket, s), content_type='text/xml')
        else:
            logging.debug('invalid user detected username: %s password %s' % (username, password))
            return HttpResponse(failed, content_type='text/xml')

    if ticket is not None:
        t = QWCTicket.objects.get(ticket=ticket.text)
        if t is not None:
            # all_fancy_stuff = cont.find(tag('strHCPResponse')).text
            profile = None
            company_file_location = cont.find(tag('strCompanyFileName'))

            # update the company_file location if it's not updated.
            try:
                profile = t.user.userprofile
            except Exception as e:
                profile = UserProfile.objects.create(user=t.user)
            if company_file_location is not None:
                if company_file_location != profile.company_file:
                    profile.company_file = company_file_location.text
                    profile.save()

        logging.debug("Dealing with ticket: %s" % (ticket.text))
        receive_response = root[0].find(tag('receiveResponseXML'))
        logging.debug(root.findall(tag('receiveResponseXML')))
        logging.debug(root.find(tag('receiveResponseXML')))
        logging.debug(root.findtext(tag('receiveResponseXML')))
        send_request = root[0].find(tag('sendRequestXML'))
        logging.debug(send_request)
        if send_request != None:
            logging.debug("sendRequestXML detected tags will appear below:")
            for child in send_request:
                logging.debug(child.tag)
            mq = MessageQue.objects.filter(user=t.user, active=True)
            if len(mq) != 0:
                logging.debug("MessageQue has one or more messages awaiting")
                m = mq[0]
                ms = m.message
                logging.debug("sending message in que: %s" % (m.id))

                # Mark message as consumed
                m.active = False
                m.save()
                return HttpResponse(qrequest % (xml_soap(ms)), content_type='text/xml')
            else:
                logging.debug("No message in messageQue")
                logging.info("activating everything that is set to repeat")
                logging.debug('Finished')
                repeats = MessageQue.objects.filter(repeat=True, active=False)
                for repeat in repeats:
                    repeat.active = True
                    repeat.save()
                return HttpResponse(close_connection % ("Finished!"), content_type='text/xml')

            return HttpResponse(close_connection % (100), content_type='text/xml')
        else:
            logging.debug("sendRequestXML Not detected")

        if receive_response != None:
            logging.debug(receive_response.text)
            tick = QWCTicket.objects.get(ticket=ticket.text)
            response = receive_response[1].text
            receive_plain = etree.fromstring(response)
            receive_query_name = etree.fromstring(response)[0][0].tag[:-2]
            if response != None:
                logging.debug('response is %s' % (response))
                resp = ReceiveResponse.objects.create(ticket=tick, response=response, name=receive_query_name)
                # Let's try to do something with this response now!
                qn = receive_query_name[:-5]
                logging.info("THAT IS ===> %s" %(qn))
                if qn in QBXML().names:
                    # does that model exists ?
                    ms = get_models()
                    m = None
                    for model in ms:
                        if model.__name__ == 'QB' + qn:
                            m = model
                    if m != None:
                        items = receive_plain[0][0]
                        for item in items:
                            t = {}
                            for it in item:
                                t.update({convert(it.tag): it.text})
                            m.objects.create(**t)

                return HttpResponse(close_connection % ('ssss'), content_type='text/xml')
        else:
            logging.debug("This message does not contain response")
    logging.info("Calling close")
    return HttpResponse(close_connection % ('closed!!!'), content_type='text/xml')


def welcome(request):
    return HttpResponse('<h1>Use /quickbooks</h1>', content_type='text/html')

def get_company_file(request):
    response = HttpResponse(generate_qbc_file(), content_type='text/xml')
    response['Content-Disposition'] = 'attachment; filename="quickbooks"'