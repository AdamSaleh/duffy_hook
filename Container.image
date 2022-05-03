FROM fedora:35
RUN dnf -y install python3-uvicorn python3-fastapi
WORKDIR /opt
COPY ./duffy_hook /opt/duffy_hook
CMD ["uvicorn", "duffy_hook.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
