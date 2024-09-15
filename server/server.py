# server/server.py
from flask import Flask, request, jsonify, render_template
from concrete import fhe
import base64

app = Flask(__name__)


@fhe.compiler({"x": "encrypted"})
def add_42(x):
    return x + 42


inputset = range(10)
circuit = add_42.compile(inputset)
server = circuit.server


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get_client_specs", methods=["GET"])
def get_client_specs():
    return jsonify(
        {"client_specs": base64.b64encode(server.client_specs.serialize()).decode()}
    )


@app.route("/compute", methods=["POST"])
def compute():
    data = request.json
    encrypted_input = fhe.Value.deserialize(base64.b64decode(data["encrypted_input"]))
    evaluation_keys = fhe.EvaluationKeys.deserialize(
        base64.b64decode(data["evaluation_keys"])
    )

    print("Received encrypted input:", data["encrypted_input"])

    result = server.run(encrypted_input, evaluation_keys=evaluation_keys)

    encrypted_result = base64.b64encode(result.serialize()).decode()
    print("Computed result (encrypted):", encrypted_result)

    return jsonify({"result": encrypted_result})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
