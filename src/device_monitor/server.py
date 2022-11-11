from glob import glob
import socket
from flask import Flask, jsonify, render_template, request
import pandas as pd

HOSTNAME = socket.gethostname()
IP = socket.gethostbyname(HOSTNAME)
port = 5000
path_log = ""


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", host=HOSTNAME, ip=IP, port=port)


@app.route("/data")
def data():
    paths = glob(path_log + "*")
    paths.sort()
    if len(paths) > 1:
        paths = paths[1:] + paths[:1]

    df = pd.concat([pd.read_csv(path, header=None) for path in paths], axis=0, ignore_index=True)

    duration = int(request.args.get("duration"))
    if duration:
        df = df[df.values[-1,0] - df.iloc[:,0] < duration]

    timestamp = df.values[:,0].tolist()
    memory = (df.values[:,2] / df.values[:,1] * 100).tolist()

    num_cpu = df.values[0, 5]
    cpus = df.values[:,6:6+num_cpu].T.tolist()

    names_disks = df.values[0, 7 + num_cpu::4]
    values_disks = (df.values[:, 9 + num_cpu::4] / df.values[:, 8 + num_cpu::4] * 100).T.tolist()
    disks = {name: value for name, value in zip(names_disks, values_disks)}

    return jsonify({
        "timestamp": timestamp,
        "memory": memory,
        "cpus": cpus,
        "disks": disks,
    })


def main():
    global path_log, port
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("log", type=str)
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    path_log = args.log
    port = args.port

    app.run(host="0.0.0.0", port=port)
