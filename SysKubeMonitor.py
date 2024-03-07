# [root@mtx-app-prd2-5 scripts]# cat SysKubeMonitor.py
#!/usr/bin/env python3
from email import message
import os
import subprocess
import logging
import socket
# import sys
from textwrap import wrap
# import time
import datetime
from datetime import date
# import re
## from typing_extensions import reveal_type
import psutil
import argparse
from collections import Counter
# import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from subprocess import Popen, PIPE
from prettytable import PrettyTable as pt

# import xlsxwriter
# import textfsm
# import texttable
# from tabulate import tabulate
# table = texttable.Texttable()
# table.set_cols_align(["l", "r", "c","r"])
#table.set_cols_valign(["t", "m", "b","b"])


table = pt(["Name", "Status", "Restarts", "Node"])
table1 = pt()

table = pt(["Node_Name", "Status", "Role"])
table2 = pt()

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


def check_cpu_spike(file_name):
    title = "High CPU spike "
    # file_name = '/tmp/daily_report.txt'
    cpu_percent=psutil.cpu_percent()
    local_time_zone= str(datetime.datetime.utcnow().astimezone().tzinfo)
    current_datetime=((datetime.datetime.now()).strftime("%c"))+' '+local_time_zone

    if cpu_percent > 80:
        message=f"CPU_Percent greater than 80%: {str(round(cpu_percent,2))} : Timestamp: {current_datetime}."
        with open(file_name, 'a') as cpu_status_report:
            cpu_status_report.write("\n---------------------------------------------------------------------------------------------------------")
            cpu_status_report.write(title)
            cpu_status_report.write(message)
            cpu_status_report.write("\n---------------------------------------------------------------------------------------------------------")
        logging.debug(message)
        # send_mail(title, mails_list,file_name)
    else:
        message=f"CPU_Percent: {str(round(cpu_percent,2))} : Timestamp: {current_datetime}."
        logging.debug(message)


def check_ram_usage(file_name):
    title = "High Memory Utilization "
    # file_name = '/tmp/daily_report.txt'
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
        with open(file_name, 'a') as memory_report:
            memory_report.write(title)
            memory_report.write(message)
            memory_report.write("\n---------------------------------------------------------------------------------------------------------")
        # send_mail(title, mails_list,file_name)
    else:
        message=f"Memory utilization: {str(round(percentage_used,2))} : Timestamp: {current_datetime}."
        logging.debug(message)


def check_storage(file_name):
    """
    Get disk usage information for the root partition '/' and external partition '/apps'
    """
    try:

        root_partition = '/'
        external_partition = '/apps'

        # 1: Check Root Storage Utilization
        usage = psutil.disk_usage(root_partition)

        root_total_space = usage.total / (1024 ** 3)  # Total space in GB
        root_used_space = usage.used / (1024 ** 3)    # Used space in GB
        root_free_space = usage.free / (1024 ** 3)    # Free space in GB
        root_space_percent = usage.percent            # Percentage of space used

        status_message1 = f"\n\n=================Root Storage ({root_partition}) status=================\n"
        status_message1 += f"\tTotal Space: {root_total_space:.2f} GB\n"
        status_message1 += f"\tUsed Space: {root_used_space:.2f} GB\n"
        status_message1 += f"\tFree Space: {root_free_space:.2f} GB\n"
        if root_space_percent > 80:
            status_message1 += f"\tSpace Used: {root_space_percent}% ***High Storage Utilization : Need Immediate Action***"
        else:
            status_message1 += f"\tSpace Used: {root_space_percent}%"

        # 2: Check External Storage Utilization
        usage = psutil.disk_usage(external_partition)

        ext_total_space = usage.total / (1024 ** 3)  # Total space in GB
        ext_used_space = usage.used / (1024 ** 3)    # Used space in GB
        ext_free_space = usage.free / (1024 ** 3)    # Free space in GB
        ext_space_percent = usage.percent            # Percentage of space used

        status_message2 = f"\n=================External Storage ({external_partition}) status=================\n"
        status_message2 += f"\tTotal Space: {ext_total_space:.2f} GB\n"
        status_message2 += f"\tUsed Space: {ext_used_space:.2f} GB\n"
        status_message2 += f"\tFree Space: {ext_free_space:.2f} GB\n"
        if ext_space_percent > 80:
            status_message2 += f"\tSpace Used: {ext_space_percent}% ***High Storage Utilization : Need Immediate Action***"
        else:
            status_message2 += f"\tSpace Used: {ext_space_percent}%"

        with open(file_name, 'a') as storage_report:
            storage_report.write(f'\n{status_message1}\n')
            storage_report.write(f'\n{status_message2}\n')

    except Exception as e:
        return f"Error checking root partition status: {e}"

def check_matrix_pods(html_file_name):
    check_pods_cmd = "kubectl get pod -n matrix-ns -o wide | awk '{print $1, $3, $4, $7}'"
    pods_output = subprocess.check_output(check_pods_cmd, shell=True)
    logging.debug(pods_output)
    pods_lines = pods_output.decode("utf-8").splitlines()
    pods_list=[]

    local_time_zone= str(datetime.datetime.utcnow().astimezone().tzinfo)
    current_datetime=((datetime.datetime.now()).strftime("%c"))+' '+local_time_zone

    pods_evicted_list=[]
    table1.field_names = ["NAME_SPACE","NAME","STATUS","RESTARTS",'NODE']
    table1.align['NAME_SPACE']='c'
    table1.align['NAME']='c'
    table1.align['STATUS']='c'
    table1.align['RESTARTS']='r'
    table1.align['NODE']='r'
    with open(file_name, 'a') as pods_status_report:
        for i in range(1,len(pods_lines)):
            pods_dict={}
            pods_status = pods_lines[i].split( )
            if pods_status[2]!='Running' and pods_status[2]!='Completed':
                if  pods_status[2]=='Evicted':
                    pods_evicted_list.append(pods_status[1])

                    pods_dict['name_space']="matrix-ns"
                    pods_dict['name']=pods_status[0]
                    pods_dict['status']=pods_status[1]
                    pods_dict['restarts']=pods_status[2]
                    pods_dict['node']=pods_status[3]

                    pods_list.append(pods_dict)
                    new_line='\n'
                    data=(f"Pods_Namespace : {str(pods_status[0])}, Pods_Name :{str(pods_status[1])}, Pods_Status: {str(pods_status[2])},Restarts: {str(pods_status[3])},Node: {str(pods_status[4])}, Timestamp: {current_datetime}. {new_line}")
                    table1.add_row(["matrix-ns",str(pods_status[0]),str(pods_status[1]),str(pods_status[2]),str(pods_status[3])])

                    #pods_status_report.write('\n'+data)
                    logging.debug(data)
                else:
                    print('not evicted status')
                    pods_dict['name_space']="matrix-ns"
                    pods_dict['name']=pods_status[0]
                    pods_dict['status']=pods_status[1]
                    pods_dict['restarts']=pods_status[2]
                    pods_dict['node']=pods_status[3]

                    pods_list.append(pods_dict)
                    new_line='\n'
                    data=(f"Pods_Namespace : matrix-ns, Pods_Name :{str(pods_status[0])}, Pods_Status: {str(pods_status[1])},Restarts: {str(pods_status[2])},Node: {str(pods_status[3])}, Timestamp: {current_datetime}. {new_line}")
                    table1.add_row(["matrix-ns",str(pods_status[0]),str(pods_status[1]),str(pods_status[2]),str(pods_status[3])])

                    #pods_status_report.write('\n'+data)
                    logging.debug(data)

    body=table1.get_html_string()
    with open(html_file_name, 'a') as mail_file:
        mail_file.write('\n<br><br>================= Matrix Pods Status=================<br><br>')
        mail_file.write('\n'+body)
        mail_file.write('\n<br>\n')


def check_kubernetes_pods(html_file_name):
    check_pods_cmd = "kubectl get pod -n kube-system -o wide | awk '{print $1, $3, $4, $7}'"
    pods_output = subprocess.check_output(check_pods_cmd, shell=True)
    logging.debug(pods_output)
    pods_lines = pods_output.decode("utf-8").splitlines()
    pods_list=[]

    local_time_zone= str(datetime.datetime.utcnow().astimezone().tzinfo)
    current_datetime=((datetime.datetime.now()).strftime("%c"))+' '+local_time_zone

    pods_evicted_list=[]
    table1.field_names = ["NAME_SPACE","NAME","STATUS","RESTARTS",'NODE']
    table1.align['NAME_SPACE']='c'
    table1.align['NAME']='c'
    table1.align['STATUS']='c'
    table1.align['RESTARTS']='r'
    table1.align['NODE']='r'
    with open(html_file_name, 'a') as pods_status_report:
        for i in range(1,len(pods_lines)):
            pods_dict={}
            pods_status = pods_lines[i].split( )
            if pods_status[2]!='Running' and pods_status[2]!='Completed':
                if  pods_status[2]=='Evicted':
                    pods_evicted_list.append(pods_status[1])

                    pods_dict['name_space']='kube-system'
                    pods_dict['name']=pods_status[0]
                    pods_dict['status']=pods_status[1]
                    pods_dict['restarts']=pods_status[2]
                    pods_dict['node']=pods_status[3]

                    pods_list.append(pods_dict)
                    new_line='\n'
                    data=(f"Pods_Namespace : kube-system, Pods_Name :{str(pods_status[0])}, Pods_Status: {str(pods_status[1])},Restarts: {str(pods_status[2])},Node: {str(pods_status[3])}, Timestamp: {current_datetime}. {new_line}")
                    table1.add_row(['kube-system',str(pods_status[0]),str(pods_status[1]),str(pods_status[2]),str(pods_status[3])])

                    #pods_status_report.write('\n'+data)
                    logging.debug(data)
                else:
                    print('not evicted status')
                    pods_dict['name_space']='kube-system'
                    pods_dict['name']=pods_status[0]
                    pods_dict['status']=pods_status[1]
                    pods_dict['restarts']=pods_status[2]
                    pods_dict['node']=pods_status[2]

                    pods_list.append(pods_dict)
                    new_line='\n'
                    data=(f"Pods_Namespace : kube-system, Pods_Name :{str(pods_status[0])}, Pods_Status: {str(pods_status[1])},Restarts: {str(pods_status[2])},Node: {str(pods_status[3])}, Timestamp: {current_datetime}. {new_line}")
                    table1.add_row(['kube-system',str(pods_status[0]),str(pods_status[1]),str(pods_status[2]),str(pods_status[3])])

                    #pods_status_report.write('\n'+data)
                    logging.debug(data)

    body=table1.get_html_string()
    with open(html_file_name, 'a') as mail_file:
        mail_file.write('\n<br><br>=================Kubernetes Pods Status=================<br><br>')
        mail_file.write('\n'+body)
        mail_file.write('\n<br>\n')


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
    file_name = '/tmp/daily_report.txt'
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
        with open(html_file_name, 'a') as mail_file:
            mail_file.write('\n<br><br>=================Pods Running Status=================<br><br>')
            mail_file.write('\n'+body)
            mail_file.write('\n<br>\n')


def check_node_status(html_file_name):
    title = ": Cluster Node Status"
    check_node_cmd = "kubectl get nodes | awk '{print $1, $2, $3}'"
    node_output = subprocess.check_output(check_node_cmd, shell=True)
    logging.debug(node_output)
    node_lines = node_output.decode("utf-8").splitlines()
    node_list=[]
    local_time_zone= str(datetime.datetime.utcnow().astimezone().tzinfo)
    current_datetime=((datetime.datetime.now()).strftime("%c"))+' '+local_time_zone
    table2.field_names = ["NODE_NAME","STATUS","ROLE"]
    table2.align['NODE_NAME']='c'
    table2.align['STATUS']='c'
    table2.align['ROLE']='r'
    for i in range(1,len(node_lines)):
        node_dict={}
        node_status = node_lines[i].split( )
        if node_status[1] == 'NotReady':
            node_dict['node_name']=node_status[0]
            node_dict['status']=node_status[1]
            node_dict['role']=node_status[2]

            node_list.append(node_dict)
            new_line='\n'
            data=(f"node_name : {str(node_status[0])}, status :{str(node_status[1])}, role: {str(node_status[2])}, Timestamp: {current_datetime}. {new_line}")
            table2.add_row([str(node_status[0]),str(node_status[1]),str(node_status[2])])
            logging.debug(data)

    body = "<br><br>=================Cluster Node Status=================<br><br>"
    body += table2.get_html_string()


    if len(node_list)!=0:
        with open(html_file_name, 'a') as mail_file:
            mail_file.write('\n<br><br>=================Cluster Node Status=================<br><br>')
            mail_file.write('\n'+body)
            mail_file.write('\n<br>\n')


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


def timescale_db_status(file_name):
    """
    Check Timescale DB monitoring (Master Node, Replica Lag and Wal/Data folder size)
    """
    # Variable delcaration for DB monitoring
    master_db_details = "DB switch over monitoring :\n"
    lag_details = "Replica lag monitoring - (Threshold value for lag is 15mins)\n"
    wal_data_size_details = "WAL and Data folder size monitoring : (Threshold value is 1TB)"

    # Monitor for each DB
    for i in range(0, 3):
        # 1:Check if the Timescale DB node is running
        shell_command = "kubectl get pods -n matrix-ns | grep timescaledb-" + str(i) + " | awk '{print $1, $3}'"
        cert_check_output = subprocess.check_output(shell_command, shell=True, universal_newlines=True).strip().split()

        if cert_check_output[1] == "Running":
            role_command = "kubectl describe pod  -n matrix-ns timescaledb-" + str(i) + " | grep role="
            tsdb_role = subprocess.check_output(role_command, shell=True, universal_newlines=True).strip().split("role=")
            if tsdb_role[1]:
                # 2:Check for Replica Node
                if tsdb_role[1] == "replica":
                    # 3:Monitor Replica Node Lag
                    lag_command = """kubectl exec -it -n matrix-ns timescaledb-""" + str(i) + """ timescaledb -- bash -c "psql -U matrixnis -c 'SELECT pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn() AS synced, (EXTRACT(EPOCH FROM now()) -EXTRACT(EPOCH FROM pg_last_xact_replay_timestamp()))::int AS lag;'" """
                    tsdb_lag = subprocess.check_output(lag_command, shell=True, universal_newlines=True).strip().split("role=")
                    if tsdb_lag:
                        lag = tsdb_lag[0].strip().replace(" ", "").split("\n")[2][-1:]
                        lag_details += "\t timescaledb-" + str(i) + f" : {lag} sec \n"
                # 4:Check for Master Node
                elif tsdb_role[1] == "master":
                    master_db_details += "\ttimescaledb-" + str(i) + " is Master!\n"
                    db_master_node = "timescaledb-" + str(i)

        # 5:Monitor the Wal and Data size
        wal_data_command = f"kubectl exec -it -n matrix-ns timescaledb-{str(i)} timescaledb -- bash -c 'du -sh /var/lib/postgresql/wal /var/lib/postgresql/data'"
        wal_data_size = subprocess.check_output(wal_data_command, shell=True, universal_newlines=True)
        wal_data_size_details += "\n\ttimescaledb-" + str(i) +" :"
        for data in wal_data_size.split("\n"):
            wal_data_size_details += "\n\t\t" + data

    # Write the collected data to the temp file
    with open(file_name, 'a') as tsdb_status_report:
        tsdb_status_report.write('\n=================Timescale DB Status=================\n')
        tsdb_status_report.write('\n'+master_db_details)
        tsdb_status_report.write('\n'+lag_details)
        tsdb_status_report.write('\n'+wal_data_size_details)
        tsdb_status_report.write('\n')

    return db_master_node


def fps_summery(file_name):
    """
    Check FPS Summery for all three NetFlow Pipelines and  total FPS count
    """
    # Variable delcaration for FPS monitoring
    total_fps = 0

    # Check all running flows on instance
    get_vflow_command = "kubectl get pods -n matrix-ns | grep vflow | awk '{print $1, $3}'"
    vflow_details = subprocess.check_output(get_vflow_command, shell=True, universal_newlines=True).strip().split("\n")

    # Open file in to write
    with open(file_name, 'a') as fps_report:
        fps_report.write('\n=================NetFlow Pipelines FPS Status=================\n')
        fps_report.write('\nFPS count for each pipeline:\n')

        i = 1
        for data in vflow_details:
            vflow = data.split()
            # Check if the Vflow is running
            if vflow[1] == "Running":
                # Check the Netflow incoming data on each Vflow
                check_fps_command = "kubectl exec -it -n matrix-ns " + vflow[0] + """ -- sh -c "tail -100 vflow.log | grep records" | awk '{print $NF}'"""
                result = subprocess.check_output(check_fps_command, shell=True, universal_newlines=True).strip().split("\n")[-1:]

                if result[0].isnumeric():
                    # Calculate FPS value
                    fps = int((int(result[0])/60)*20)
                    # Write the collected data to the temp file
                    fps_report.write(f'\n\tPipeline-{i} : '+ str(fps))
                    # Update total FPS
                    total_fps += fps
                else:
                    fps_report.write(f'\n\tPipeline-{i} : Value Not Found')
            i += 1

        # Write the total FPS data to the temp file
        fps_report.write('\n\n\tTotal FPS Value : '+ str(total_fps) + '\n')


def aggregated_job_details(file_name, db_master_node):
    """
    Check aggregated job details in Timescale DB
    """
    # Check for timescale db master node
    if "timescaledb" in db_master_node:
        aggregation_command = f"""sudo kubectl exec -it -n matrix-ns {db_master_node} timescaledb -- psql -U matrixnis -c "select last_run_duration FROM timescaledb_information.job_stats t1, timescaledb_information.jobs t2 where t1.job_id= t2.job_id and t2.application_name like 'Refresh Continuous Aggregate Policy%';" """
        aggregation_details = subprocess.check_output(aggregation_command, shell=True, universal_newlines=True).strip().split("\n")

        # Open file in to write
        with open(file_name, 'a') as agg_report:
            agg_report.write('\n=================Timescale DB Aggregated Job Details=================\n')
            agg_report.write('\nAggregated job details in Timescale DB:\n')
            if int(aggregation_details[2:-1][-1].split(':')[1]) < 2:
                agg_report.write(f'\n\t{aggregation_details[2]} : Within Limit\n')
            else:
                agg_report.write(f'\n\t{aggregation_details[2]} : ***More than Limit 2 Mins : Critial***\n')


def docker_service_status(file_name):
    """
    Check the status of Docker Service
    """
    with open(file_name, 'a') as file_obj:
        file_obj.write('\n=================Docker Service Status=================\n')
        # Check the status of Docker Service
        status = subprocess.call(["systemctl", "is-active", "--quiet", "docker"])
        if status == 0:
            file_obj.write('\nDocker Service is : Running\n')
        else:
            file_obj.write('\nDocker Service is : Down\n')

def etcd_service_status(file_name):
    """
    Check the status of ETCD Service
    """
    with open(file_name, 'a') as file_obj:
        file_obj.write('\n=================ETCD Service Status=================\n')
        # Check the status of ETCD Service
        status = subprocess.call(["systemctl", "is-active", "--quiet", "etcd"])
        if status == 0:
            file_obj.write('\nETCD Service is : Running\n')
        else:
            file_obj.write('\nETCD Service is : Down\n')


def kubelet_service_status(file_name):
    """
    Check the status of Kubelet Service
    """
    with open(file_name, 'a') as file_obj:
        file_obj.write('\n=================Kubelet Service Status=================\n')
        # Check the status of Kubelet Service
        status = subprocess.call(["systemctl", "is-active", "--quiet", "kubelet"])
        if status == 0:
            file_obj.write('\nKubelet Service is : Running\n')
        else:
            file_obj.write('\nKubelet Service is : Down\n')


def firewalld_service_status(file_name):
    """
    Check the status of Firewalld Service
    """
    with open(file_name, 'a') as file_obj:
        file_obj.write('\n=================Firewalld Service Status=================\n')
        # Check the status of Firewalld Service
        status = subprocess.call(["systemctl", "is-active", "--quiet", "firewalld"])
        if status == 0:
            file_obj.write('\nFirewalld Service is : Running\n')
        else:
            file_obj.write('\nFirewalld Service is : Down\n')


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

    file_name = '/tmp/daily_report.txt'
    html_file_name = '/tmp/html_email.txt'
    title = "Daily Health Report : Cisco-IT Matrix"

    logging.basicConfig(filename='/tmp/debug.log', level=logging.DEBUG)
    hostname = socket.gethostname()

    # Get local timestamp
    local_time_zone= str(datetime.datetime.utcnow().astimezone().tzinfo)
    current_datetime=((datetime.datetime.now()).strftime("%c"))+' '+local_time_zone

    # ===================================================================================================================
    # 1: Check and remove if file exist
    if os.path.exists(file_name):
        os.remove(file_name)

    if 'prd2' in hostname:
        server_dc = "ALLN Prod"
    elif 'prd4' in hostname:
        server_dc = "AER Prod"
    # Open file in to write
    with open(file_name, 'w') as email_report:
        email_report.write(f'Hi All,\nPlease find below status of Critical metrics for Netflow and MDT application on {server_dc} Server!')

    # ===================================================================================================================
    # 2: Check and remove if html file exist
    if os.path.exists(html_file_name):
        os.remove(html_file_name)

    # Open file in to write
    with open(html_file_name, 'w') as html_report:
        html_report.write(f'\n<br>Hi All,<br>Please find below status of Critical metrics for Netflow and MDT application  on {server_dc} Server!<br>')

    # ===================================================================================================================
    # Start gathering the data
    # 1:Check Host Parameteres
    check_cpu_spike(file_name)
    check_ram_usage(file_name)
    check_storage(file_name)

    # 2:Check service status
    docker_service_status(file_name)
    etcd_service_status(file_name)
    kubelet_service_status(file_name)
    firewalld_service_status(file_name)

    # 3:To retrive kubernetes level details Check if host is master node or not
    result = stat = subprocess.call(["systemctl", "is-active", "--quiet", "etcd"])
    if result == 0:
        # Run below function only if host is master
        if server_type != "none":
            # 4:Check Pods and Nodes Status
            check_node_status(html_file_name)
            check_kubernetes_pods(html_file_name)
            check_matrix_pods(html_file_name)
            matrix_pods_count(server_type)
            # 5:Check for kubeadm certificate expiration
            check_certificate_expiration()

            # 6:Check Matrix Application Services
            db_master_node = timescale_db_status(file_name)
            fps_summery(file_name)
            if "timescaledb" in db_master_node:
                aggregated_job_details(file_name, db_master_node)

    # ===================================================================================================================
    # 1: Send email to all E-mail IDs
    with open(file_name, 'a') as email_report:
        email_report.write(f'\n\nRegards,\nSystem Admin : {hostname}\nTimestamp : {current_datetime}')

    if os.path.isfile(file_name) and os.stat(file_name).st_size != 0:
       send_mail(title, mails_list,file_name)

    # 2: Send email with tables to all E-mail IDs
    with open(html_file_name, 'a') as html_report:
        html_report.write(f'<br><br>Regards,<br>System Admin : {hostname}<br> Timestamp : {current_datetime}')

    if os.path.isfile(html_file_name) and os.stat(html_file_name).st_size != 0:
        #open text file in read mode
        html_body = open(html_file_name, "r").read()
        send_table_mail(mails_list, title, html_body)
