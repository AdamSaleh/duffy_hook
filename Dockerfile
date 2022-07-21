FROM fedora:35
RUN dnf -y install python3-uvicorn ansible python3-fastapi python3-pip
RUN pip install python-cicoclient paramiko
WORKDIR /opt
COPY . /opt/duffy_hook
WORKDIR /opt/duffy_hook
#CMD ["uvicorn", "duffy_hook.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8080"]
CMD ["python3", "duffy_hook/main.py"]
