#!/usr/bin/env python3

from email import message
import os
import subprocess
import logging
import socket
import sys
from textwrap import wrap
import time
import datetime
from datetime import date
import re
## from typing_extensions import reveal_type
import psutil
import argparse

from collections import Counter

import pandas as pd

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from subprocess import Popen, PIPE

# import xlsxwriter
# import textfsm
# import texttable
# from tabulate import tabulate
# table = texttable.Texttable()
# table.set_cols_align(["l", "r", "c","r"])
#table.set_cols_valign(["t", "m", "b","b"])


from prettytable import PrettyTable as pt

table = pt(["Name", "Status", "Restarts", "Node"])
table1=pt()


def send_mail(title, mails_list,file_name):
    for i in range(len(mails_list)):
        mail_id=mails_list[i]
        hostname = socket.gethostname()
        mail_command = f'mail -s "{hostname}: {title}" {mail_id} < {file_name}'
        os.system(mail_command)

def send_table_mail(send_to_address, subject, body):

    for i in send_to_address:
        css = """
        <style>
        table, th, td {
            border: 1px solid black;
            border-collapse: collapse;
        }
        </style>
        """
        msg = MIMEText(css+body,'html')
        msg["From"] = socket.gethostname()
        msg["To"] = i
        msg["Subject"] = subject

        p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
        p.communicate(msg.as_bytes())




def check_cpu_spike():
    title = ": High CPU spike "
    file_name = '/tmp/cpu_spike_info.txt'
    cpu_percent=psutil.cpu_percent()


    local_time_zone= str(datetime.datetime.utcnow().astimezone().tzinfo)
    current_datetime=((datetime.datetime.now()).strftime("%c"))+' '+local_time_zone

    if cpu_percent>80:
        message=f"CPU_Percent greater than 80%: {str(round(cpu_percent,2))} : Timestamp: {current_datetime}."

        with open(file_name, 'w') as cpu_status_report:
            cpu_status_report.write(message)
        logging.debug(message)
        send_mail(title, mails_list,file_name)
    else:
        message=f"CPU_Percent: {str(round(cpu_percent,2))} : Timestamp: {current_datetime}."
        logging.debug(message)




def check_ram_usage():
    title = ": High Memory Utilization "
    file_name = '/tmp/memory_info.txt'
    check_free_cmd = 'free'
    memory_output = subprocess.check_output(check_free_cmd, shell=True)
    logging.debug(memory_output)
    lines = memory_output.decode("utf-8").splitlines()
    columns = lines[0].split()
    memory = lines[1].split()[1:]
    output_dict = dict(zip(columns, memory))

    percentage_used = 100*int(output_dict['used'])/int(output_dict['total'])


    local_time_zone= str(datetime.datetime.utcnow().astimezone().tzinfo)
    current_datetime=((datetime.datetime.now()).strftime("%c"))+' '+local_time_zone



    if percentage_used > 80:
        message=f"Memory utilization greater than 80%: {str(round(percentage_used,2))} : Timestamp: {current_datetime}."
        logging.debug(message)
        with open(file_name, 'w') as memory_report:
            memory_report.write(message)
        send_mail(title, mails_list,file_name)
    else:
        message=f"Memory utilization: {str(round(percentage_used,2))} : Timestamp: {current_datetime}."
        logging.debug(message)


def check_storage():
    title = ': High Storage Utilization'
    check_storage_cmd = 'df -h'
    storage_data = subprocess.check_output(check_storage_cmd, shell=True)
    lines = storage_data.decode("utf-8").splitlines()
    columns = lines[0].split()[1:]

    file_name = '/tmp/storage_mail.txt'

    local_time_zone= str(datetime.datetime.utcnow().astimezone().tzinfo)
    current_datetime=((datetime.datetime.now()).strftime("%c"))+' '+local_time_zone


    if os.path.exists(file_name):
        os.remove(file_name)
    i = -1
    alert = False
    for line in lines[1:]:
        row = line.split()
        row_dict = dict(zip(columns, row[1:]))
        if int(row_dict['Use%'].strip('%')) > 80:
            alert = True
            if i == -1:
                file_data = f'High Storage Usage Report, storage is high on following filesystems: \n'
                with open(file_name, 'a') as mail_file:
                    mail_file.write(file_data)
                i = i + 1
            if not 'lib' in row[-1]:
                message=f"Filesystem {str(row[0])} mounted on {str(row[-1])},current usage: {row_dict['Use%']} ,Timestamp: {current_datetime}."
                logging.debug(message)
                with open(file_name, 'a') as mail_file:
                    mail_file.write('\n'+message)
            else:
                message=f"Filesystem {str(row[0])} mounted on {str(row[-1])},current usage: {row_dict['Use%']} ,Timestamp: {current_datetime}."
                logging.debug(message)


        else:
            continue
    if alert:
        send_mail(title, mails_list,file_name)

def check_pods():
    title = ": Pods Status"
    file_name = '/tmp/pods_eviction_info1.txt'
    check_pods_cmd = "kubectl get pod -A -o wide | awk '{print $1, $2, $4, $5, $8}'"
    pods_output = subprocess.check_output(check_pods_cmd, shell=True)
    logging.debug(pods_output)
    pods_lines = pods_output.decode("utf-8").splitlines()
    pods_list=[]

    local_time_zone= str(datetime.datetime.utcnow().astimezone().tzinfo)
    current_datetime=((datetime.datetime.now()).strftime("%c"))+' '+local_time_zone

    if os.path.exists(file_name):
        os.remove(file_name)
    pods_evicted_list=[]
    table1.field_names = ["NAME_SPACE","NAME","STATUS","RESTARTS",'NODE']
    table1.align['NAME_SPACE']='c'
    table1.align['NAME']='c'
    table1.align['STATUS']='c'
    table1.align['RESTARTS']='r'
    table1.align['NODE']='r'
    with open(file_name, 'w') as pods_status_report:

        for i in range(1,len(pods_lines)):
            pods_dict={}
            pods_status = pods_lines[i].split( )
            if pods_status[2]!='Running' and pods_status[2]!='Completed':
                if  pods_status[2]=='Evicted':
                    pods_evicted_list.append(pods_status[1])

                    pods_dict['name_space']=pods_status[0]
                    pods_dict['name']=pods_status[1]
                    pods_dict['status']=pods_status[2]
                    pods_dict['restarts']=pods_status[3]
                    pods_dict['node']=pods_status[4]

                    pods_list.append(pods_dict)
                    new_line='\n'
                    data=(f"Pods_Namespace : {str(pods_status[0])}, Pods_Name :{str(pods_status[1])}, Pods_Status: {str(pods_status[2])},Restarts: {str(pods_status[3])},Node: {str(pods_status[4])}, Timestamp: {current_datetime}. {new_line}")
                    table1.add_row([str(pods_status[0]),str(pods_status[1]),str(pods_status[2]),str(pods_status[3]),str(pods_status[4])])

                    #pods_status_report.write('\n'+data)
                    logging.debug(data)
                else:
                    print('not evicted status')
                    pods_dict['name_space']=pods_status[0]
                    pods_dict['name']=pods_status[1]
                    pods_dict['status']=pods_status[2]
                    pods_dict['restarts']=pods_status[3]
                    pods_dict['node']=pods_status[4]

                    pods_list.append(pods_dict)
                    new_line='\n'
                    data=(f"Pods_Namespace : {str(pods_status[0])}, Pods_Name :{str(pods_status[1])}, Pods_Status: {str(pods_status[2])},Restarts: {str(pods_status[3])},Node: {str(pods_status[4])}, Timestamp: {current_datetime}. {new_line}")
                    table1.add_row([str(pods_status[0]),str(pods_status[1]),str(pods_status[2]),str(pods_status[3]),str(pods_status[4])])

                    #pods_status_report.write('\n'+data)
                    logging.debug(data)


    # with open(file_name, 'w') as pods_status_report:
    #     pods_status_report.write(str(table1))


    body=table1.get_html_string()

    #if len(pods_evicted_list)!=0:
        #pods_evicted_list1=[]
        #for podname in pods_evicted_list:
            #podname1=podname.split('-')
            #podname2=podname1[0]+podname1[1]
            #pods_evicted_list1.append(podname2)

        #pods_evicted_count = dict(Counter(pods_evicted_list1))
        #pods_status1='Evicted'

        #pods_evicted_list2=[]
        #pods_evicted_dict1={}
        #for key,value in pods_evicted_count.items():
            #pods_evicted_dict1['Pod_Name']=key
            #pods_evicted_dict1['Status']=pods_status1
            #pods_evicted_dict1['Count']=value
            #pods_evicted_list2.append(pods_evicted_dict1)

        #pods_evicted_count=(f"Summary:{pods_evicted_list2}")
        #print(pods_evicted_count)
        #with open(file_name, 'a') as pods_status_report:
            #pods_status_report.write('\n'+pods_evicted_count)

    if len(pods_list)!=0:
        # send_mail(title, mails_list,file_name)
        send_table_mail(mails_list, title, body)



def matrix_pods_count(server_type):
    server_types ={
        'matrix': {
            'namespace': 'matrix-ns',
            'pods_length': 47
        },
        'bpa': {
            'namespace': 'bpa-ns',
            'pods_length': 104
        }
        # ,
        # 'somaf': {
        #     'namespace': 'somaf-ns',
        #     'pods_length': 2
        # }
    }
    namespace = server_types[server_type]['namespace']
    pods_length = server_types[server_type]['pods_length']
    # title = ": Pods Running Status"
    file_name = '/tmp/pods_running_info1.txt'
    #file_name1 = '/tmp/pods_running_output.xlsx'
    check_pods_cmd = f"kubectl get pods -n {namespace} | wc -l"
    pods_output = subprocess.check_output(check_pods_cmd, shell=True)
    pods_count = pods_output.decode("utf-8").splitlines()

    if int(pods_count[0])<int(pods_length):
        print('if pods count ')
        check_pods_cmd1 = "kubectl get pods -n  'matrix-ns' -o wide"
        pods_running_output = subprocess.check_output(check_pods_cmd1, shell=True)
        pods_lines = pods_running_output.decode("utf-8").splitlines()
        ##print('pods_lines....',len(pods_lines))

        local_time_zone= str(datetime.datetime.utcnow().astimezone().tzinfo)
        current_datetime=((datetime.datetime.now()).strftime("%c"))+' '+local_time_zone
        pods_list=[]

        if os.path.exists(file_name):
            os.remove(file_name)

        for i in range(1,len(pods_lines)):
                pods_dict={}
                pods_status = pods_lines[i].split( )

                if pods_status[2]!='Running' and pods_status[2]!='Completed':
                    #pods_dict['name_space']=
                    pods_dict['name']=pods_status[0]
                    pods_dict['status']=pods_status[2]
                    pods_dict['restarts']=pods_status[3]
                    pods_dict['node']=pods_status[6]

                    pods_list.append(pods_dict)

                    table.add_row([str(pods_status[0]),str(pods_status[2]),str(pods_status[3]),str(pods_status[6])])


        body=table.get_html_string()
        subject='Pods_Running_Status'
        print('len',len(pods_list))
        # with open(file_name, 'w') as pods_status_report:
        #     pods_status_report.write(str(table))

        if len(pods_list)!=0:
            send_table_mail(mails_list, subject, body)


def check_certificate_expiration():
    """
    Check Kubernetes certificate expiration and send email report.
    """
    # Run 'kubeadm certs check-expiration' command
    shell_command = "kubeadm certs check-expiration | grep 'admin.conf\|apiserver\|front-proxy-client\|controller-manager.conf\|apiserver-kubelet-client\|scheduler.conf' | awk '{print $1, $7}'"
    cert_check_output = subprocess.check_output(shell_command, shell=True, universal_newlines=True)

    # Create an HTML table to display the certificate expiration information
    send_flag = False
    html_table = f"<html><body><p>Hi Team, <br> Below Kubeadm certificates are about to expire, please take necessary action. </p><table border='1'><tr><th>Certificate</th><th>Expiration Date</th></tr>"
    for line in cert_check_output.splitlines():
        if len(line) != 0 and '!MISSING' not in line:
            if int(line.split()[1][:-1]) <= 30:
                html_table += f"<tr><td>{str(line.split()[0])}</td><td>{str(line.split()[1][:-1])}</td></tr>"
                send_flag = True
    html_table += "</table></body></html>"

    # Create the email message
    msg = MIMEMultipart()
    msg.attach(MIMEText(html_table, "html"))

    # Connect to the SMTP server and send the email
    if send_flag:
        for i in mails_list:
            msg["From"] = socket.gethostname()
            msg["To"] = i
            msg["Subject"] = "Kubernetes Certificate Expiration Report : High Priority"

            p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
            p.communicate(msg.as_bytes())


def server_type_checker(server_type):
    server_type = str(server_type)

    # if server_type in list1:
    #     return server_type
    if server_type== 'matrix' :
        return server_type
    elif  server_type == 'bpa':
        return server_type
    # elif  server_type == 'none':
    #     return server_type
    else:
        raise argparse.ArgumentTypeError('please server_type matrix or bpa!!!')
    return server_type

if __name__ == '__main__':
    description='''
    This script is checking the health status of matrix servers like checking cpu_spike,ram_usage,storage_usage and pods_status
    It should be able to get notification about system health metrics .System metrics should be within the threshold defined.(80%)
    System storage should be within threshold defined.Otherwise get a notification about system storage.
    In check_pods if any pod is not equal to running and completed status then send a notification about pods status.

    *Python Code Run Command*
    /usr/bin/python3 check-cert-expiration.py -s matrix -m twagh@cisco.com,ajchaura@cisco.com
    '''

    my_parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    my_parser.add_argument('-m', dest='mails_list', nargs='+', type=str, default=['nws-ia-platform-alerts@cisco.com', 'ciscoit_matrix@cisco.com'],\
        help="Provide a list of email addresses to alert in case of health status is affected (separated by a whitespace)")

    my_parser.add_argument('-s', dest='server_type',  type=server_type_checker, \
        help="Specify server type: matrix, bpa,none"    )
    args = my_parser.parse_args()
    mails_list = args.mails_list
    server_type = args.server_type

    logging.basicConfig(filename='/tmp/debug.log', level=logging.DEBUG)
    hostname = socket.gethostname()

    check_cpu_spike()
    check_ram_usage()
    check_storage()

    # Check if host is master node or not
    result = stat = subprocess.call(["systemctl", "is-active", "--quiet", "etcd"])
    if result == 0:
        # Run below function only if host is master
        if server_type != "none":
            check_pods()
            matrix_pods_count(server_type)

            #Check for kubeadm certificate expiration
            check_certificate_expiration()
