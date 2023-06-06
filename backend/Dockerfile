FROM python:3.10.11-bullseye AS build
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --user -r requirements.txt

FROM python:3.10.11-bullseye
WORKDIR /app
COPY . .
COPY --from=build /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "main.py"]