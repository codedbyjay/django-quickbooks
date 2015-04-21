from django.conf.urls import patterns, include, url

from quickbooks.views import GetCompanyFileView

urlpatterns = patterns('',
    url(r'^$', 'quickbooks.views.home'),
    url(r'^wsdl$', 'quickbooks.views.show_wsdl'),
    url(r'^get-company-file', GetCompanyFileView.as_view()),
)
