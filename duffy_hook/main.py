import json
import os
import time
from typing import Optional

import schedule
import uvicorn
from cicoclient.wrapper import CicoWrapper
from execute_ansible import execute_playbook
from fabric import Connection
from fastapi import FastAPI
from fastapi import Header
from fastapi import Request

app = FastAPI()

api = CicoWrapper(
            endpoint="http://admin.ci.centos.org:8080/",
            api_key=os.environ.get("CICO_API_KEY"),
)


def enroll_duffy_as_action(extra_vars, labels, version="8-stream"):
    arch = "x86_64"
    print("Request with labels:", labels)

    # todo what if fails
    hosts, ssid = api.node_get(
        arch=arch,
        ver=version,
        count=1,
        retry_count=2,
        retry_interval=30,
    )
    print(hosts)
    key, host = hosts.popitem()
    print(key)
    print(host)
    extra_vars["github_runner_labels"] = ",".join(labels)

    # todo what if fails
    result = execute_playbook(
        inventory_string=f"{host['ip_address']},",
        extra_vars=extra_vars,
        playbook_path="./ansible/register-runner.yml",
    )
    print(result)
    return result


def clear_counts(config):
    for k in config:
        for v in config[k]['versions']:
            v['current_count'] = 0
    return config


def make_sure__there_is_enough_nodes(config):
    # get current nodes
    nodes = api.inventory()
    print("Node info - basic:")
    print(nodes)
    nodes = update_nodes_github_runner_info(nodes)
    print("Node info - with runers:")
    print(nodes)
    clear_counts(config)
    # make each node counted in the project
    for n in nodes:
        node = nodes[n]
        for running in node['github']['running']:
            v = node['centos_version']
            if v in config[running]['version']:
                config[running]['version'][v]['current_count'] += 1
    print("Config with counts")
    print(config)
    # for each project
    for k in config:
        for v in config[k]['versions']:
            if config[k][v]['current_count'] < config[k][v]['min_count']:
                print("Setting up:")
                print(
                    config[k][v],
                    config[k][v]['labels'],
                    version=v,
                )
                config[k][v]["runner_slug"] = k
                enroll_duffy_as_action(
                    config[k][v], config[k][v]['labels'],
                    version=v, arch=config[k][v]['arch'],
                )


@app.on_event("startup")
def schedule_there_is_enough_nodes() -> None:
    config = {}
    print("Scheduling")
    with open('/etc/duffy-hook/ansible_config.json') as fs:
        config = json.load(fs)
    print(config)
    make_sure__there_is_enough_nodes(config)
    schedule.every(10).minutes.do(make_sure__there_is_enough_nodes, config)

    while True:
        schedule.run_pending()
        time.sleep(1)


@app.get('/')
def read_root():
    return {'Hello': 'World'}


@app.post("/check_nodes")
def hook_there_is_enough_nodes() -> None:
    config = {}
    print("Scheduling")
    with open('/etc/duffy-hook/ansible_config.json') as fs:
        config = json.load(fs)
    print(config)
    make_sure__there_is_enough_nodes(config)


@app.get('/items/{item_id}')
def read_item(item_id: int, q: Optional[str] = None):
    return {'item_id': item_id, 'q': q}


@app.post("/enroll/{app_name}/{label}/{version}")
async def receive_enroll_duffy(app_name, label, version):
    extra_vars = {}
    with open('/etc/duffy-hook/ansible_config.json') as fs:
        extra_vars = json.load(fs)
    enroll_duffy_as_action(extra_vars[app_name][version], [label], version)


@app.post("/webhook/{app_name}")
async def receive_payload(
    request: Request,
    app_name: str,
    x_github_event: str = Header(...),
):
    print("event:", x_github_event)
    extra_vars = {}
    with open('/etc/duffy-hook/ansible_config.json') as fs:
        extra_vars = json.load(fs)

    if x_github_event == "ping":
        return {"message": "pong"}
    if x_github_event == "workflow_job":
        payload = await request.json()
        labels = payload['workflow_job']['labels']
        if 'stream-8' in labels:
            enroll_duffy_as_action(
                extra_vars[app_name]['8-stream'], labels, "8-stream",
            )
# {'n63.pufty': {'host_id': 127, 'hostname': 'n63.pufty',
# 'ip_address': '172.19.3.127', 'chassis': 'pufty',
# 'used_count': 4411, 'current_state': 'Deployed',
# 'comment': '6f76948a', 'distro': None, 'rel': None,
# 'centos_version': '8-stream', 'architecture': 'x86_64',
# 'node_pool': 1, 'console_port': 2620, 'flavor': None}}
    else:
        try:
            payload = await request.json()
            print(payload)
        except Exception as e:
            print("Couldn't get payload:", e)

        return {"message": "Unable to process action"}


def update_nodes_github_runner_info(nodes):
    for k in nodes:
        ip = nodes[k]["ip_address"]
        # getting the project from running process
        # the service name is the first word, i.e.
        # actions.runner.AdamSaleh-sig-core-t_functional.localhost.service
        result_running = Connection(ip).run(
            "systemctl --no-page"
            " | grep 'running.*GitHub Actions Runner'"
            " | awk '{print $1}'"
            " | awk -F'.' '{print $3}'", hide=True,
        )
        github = {}
        github['running'] = result_running.stdout.split("\n")

        result_all = Connection(ip).run(
            "systemctl --no-page"
            " | grep '.*GitHub Actions Runner'"
            " | awk '{print $1}'", hide=True,
        )
        github['all'] = result_all.stdout.split("\n")
        nodes[k]['github'] = github
    return nodes


@app.get("/nodes")
async def get_nodes():
    nodes = api.inventory()
    nodes = update_nodes_github_runner_info(nodes)
    return nodes


@app.delete("/node/{ssid}")
async def remove_node(ssid):
    api.node_done(ssid)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")
