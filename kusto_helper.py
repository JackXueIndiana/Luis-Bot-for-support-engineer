#encoding=utf-8

import argparse
import sys, io
import os, re, os.path
import logging
import pandas
import azure.kusto.data
from azure.kusto.data.request import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.exceptions import KustoServiceError
from azure.kusto.data.helpers import dataframe_from_result_table
import traceback
from nltk.tokenize import sent_tokenize
import requests
import json

logger = logging.getLogger()

class StringBuilder(object):
    def __init__(self):
        self._stringio = io.StringIO()
    
    def __str__(self):
        return self._stringio.getvalue()
    
    def append(self, *objects, sep=' ', end=''):
        print(*objects, sep=sep, end=end, file=self._stringio)

    def getValue(self):
        return self._stringio.getvalue()

class kustoclient:

    def __init__(self):
        self.kusto_cluster = 'Icmcluster'
        self.kusto_database = 'IcMDataWarehouse'
        self.kusto_table = 'Incidents'
        self.kusto_client = None
        self.client_id = os.environ['KUSTO_CLIENT_ID']
        self.client_secret = os.environ['KUSTO_CLIENT_SECRET']
        self.authority_id = os.environ['KUSTO_AUTHORITY_ID']

    def extractingKustoResponse(self, query = ""):
        kusto_link = "https://"+self.kusto_cluster+".kusto.windows.net"
        
        # For interactive log into Kusto ...
        KCSB = KustoConnectionStringBuilder.with_aad_device_authentication(kusto_link)
        # For AAD App log into Kusto ...
        # KCSB = KustoConnectionStringBuilder.with_aad_application_key_authentication(kusto_link, self.client_id, self.client_secret, self.authority_id)
        if not isinstance(self.kusto_client, KustoClient):
            self.kusto_client = KustoClient(KCSB)

        try:
            response = self.kusto_client.execute_query(self.kusto_database, query)
            if response is not None:
                return response
        except KustoServiceError as error:
            print("ERROR: ", error)
            traceback.print_exc()

    def run_kusto_query(self, query):
        try:
            response = self.extractingKustoResponse(query)
            if response is not None:
                data = dataframe_from_result_table(response.primary_results[0])
                return data
        except KustoServiceError as error:
            print("ERROR: ", error)
            traceback.print_exc()

    def get_recent_incidents(self):
        #query = '''cluster(\'{0}\').database(\'{1}\').[\'{2}\'] | join kind=leftanti {3} on ConversationId, DocId | project ConversationId, DocId, Subject, Body_Text'''.format(self.kusto_cluster, self.kusto_database, self.kusto_table, self.kusto_summary_table)
        query = '''cluster(\'{0}\').database(\'{1}\').[\'{2}\'] | where CreateDate > ago(1h) and Severity <= 2 | distinct CreateDate, IncidentId, Severity | order by CreateDate desc| limit 10'''.format(self.kusto_cluster, self.kusto_database, self.kusto_table)
        print(query)
        this_data = self.run_kusto_query(query)
        if this_data is not None and len(this_data) > 0:
            sb = StringBuilder()
            for k, row in this_data.iterrows():
                sb.append("CreateDate: " + row.CreateDate.strftime("%Y %m %d - %H:%M:%S.%f") + '\r\n')
                sb.append("IncidentId: " + str(row.IncidentId) + '\r\n')
                sb.append("Severity: " + str(row.Severity) + '\r\n')
                sb.append("Link: " + "https://portal.microsofticm.com/imp/v3/incidents/details/"+str(row.IncidentId)+"/home"  + '\r\n')
                sb.append('---------------------\r\n')
            return (sb.getValue())
        else:
            return ""

    def get_recent_outages(self):
        #query = '''cluster(\'{0}\').database(\'{1}\').[\'{2}\'] | join kind=leftanti {3} on ConversationId, DocId | project ConversationId, DocId, Subject, Body_Text'''.format(self.kusto_cluster, self.kusto_database, self.kusto_table, self.kusto_summary_table)
        query = '''cluster(\'{0}\').database(\'{1}\').[\'{2}\'] | where CreateDate > ago(1h) and IsOutage | distinct CreateDate, IncidentId, Severity, OutageDeclaredDate | order by CreateDate desc| limit 10'''.format(self.kusto_cluster, self.kusto_database, self.kusto_table)
        print(query)
        this_data = self.run_kusto_query(query)
        this_data = self.run_kusto_query(query)
        if this_data is not None and len(this_data) > 0:
            sb = StringBuilder()
            for k, row in this_data.iterrows():
                sb.append("CreateDate: " + row.CreateDate.strftime("%Y %m %d - %H:%M:%S.%f") + '\r\n')
                sb.append("IncidentId: " + str(row.IncidentId) + '\r\n')
                sb.append("Severity: " + str(row.Severity) + '\r\n')
                sb.append("OutageDeclaredDate: " + str(row.OutageDeclaredDate) + '\r\n')
                sb.append("Link: " + "https://portal.microsofticm.com/imp/v3/incidents/details/"+str(row.IncidentId)+"/home"  + '\r\n')
                sb.append('---------------------\r\n')
            return (sb.getValue())
        else:
            return ""
    
    def get_recent_changes(self, stguid=None, age=1):
        query = '''cluster(\'Fcmdata\').database(\'FCMKustoStore\').ChangeEvent | where ServiceTreeGuid == \'{0}\' and TIMESTAMP >= ago({1}d) | distinct TIMESTAMP, ChangeRecordId, Locations | limit 10 '''.format(stguid, age) 
        print(query)
        this_data = self.run_kusto_query(query)
        this_data = self.run_kusto_query(query)
        if this_data is not None and len(this_data) > 0:
            sb = StringBuilder()
            for k, row in this_data.iterrows():
                sb.append("TIMESTAMP: " + row.TIMESTAMP.strftime("%Y %m %d - %H:%M:%S.%f") + '\r\n')
                sb.append("ChangeRecordId: " + str(row.ChangeRecordId) + '\r\n')
                sb.append("Locations: " + str(row.Locations) + '\r\n')
                sb.append('---------------------\r\n')
            return (sb.getValue())
        else:
            return ""

    def get_incident(self, incidentid=None):
        query = '''cluster(\'{0}\').database(\'{1}\').[\'{2}\'] | where IncidentId==\'{3}\' | distinct ModifiedDate, IncidentId, Severity, Status | order by ModifiedDate desc | limit 10'''.format(self.kusto_cluster, self.kusto_database, self.kusto_table, incidentid)
        print(query)
        this_data = self.run_kusto_query(query)
        if this_data is not None and len(this_data) > 0:
            sb = StringBuilder()
            for k, row in this_data.iterrows():
                sb.append("ModifiedDate: " + row.ModifiedDate.strftime("%Y %m %d - %H:%M:%S.%f") + '\r\n')
                sb.append("IncidentId: " + str(row.IncidentId) + '\r\n')
                sb.append("Severity: " + str(row.Severity) + '\r\n')
                sb.append("Status: " + str(row.Status) + '\r\n')
                sb.append('---------------------\r\n')
            sb.append("Link: " + "https://portal.microsofticm.com/imp/v3/incidents/details/"+str(row.IncidentId)+"/home"  + '\r\n')
            return (sb.getValue())
        else:
            return ""

'''

if __name__ == '__main__':
    
    input_data = pandas.DataFrame()
    client = kustoclient()
    print(client.raw_data())
'''