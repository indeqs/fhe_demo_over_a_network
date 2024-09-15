# client/client.py
from flask import Flask, request, render_template, flash
import requests
from concrete import fhe
import base64

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a real secret key in production

BASE_URL = "http://localhost:5000"


def is_valid_input(value):
    try:
        int_value = int(value)
        return 0 <= int_value <= 63  # Adjust range as needed
    except ValueError:
        return False


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    encrypted_value = None
    if request.method == "POST":
        input_value = request.form["input"]

        if not is_valid_input(input_value):
            flash("Please enter a valid integer between 0 and 63.")
            return render_template(
                "index.html", result=result, encrypted_value=encrypted_value
            )

        input_value = int(input_value)

        try:
            # Get client specs from server
            response = requests.get(f"{BASE_URL}/get_client_specs")
            response.raise_for_status()
            client_specs = fhe.ClientSpecs.deserialize(
                base64.b64decode(response.json()["client_specs"])
            )

            # Create client and generate keys
            client = fhe.Client(client_specs)
            client.keygen()

            # Encrypt input
            encrypted_input = client.encrypt(input_value)

            # Convert encrypted input to a displayable string
            encrypted_value = base64.b64encode(encrypted_input.serialize()).decode()

            print(f"Original input: {input_value}")
            print(f"Encrypted input: {encrypted_value}")

            # Send encrypted input and evaluation keys to server
            payload = {
                "encrypted_input": encrypted_value,
                "evaluation_keys": base64.b64encode(
                    client.evaluation_keys.serialize()
                ).decode(),
            }
            response = requests.post(f"{BASE_URL}/compute", json=payload)
            response.raise_for_status()

            # Decrypt result
            encrypted_result = fhe.Value.deserialize(
                base64.b64decode(response.json()["result"])
            )

            

            result = client.decrypt(encrypted_result)

            print(f"Decrypted result: {result}")

        except requests.RequestException as e:
            flash(f"Error communicating with the server: {str(e)}")
        except Exception as e:
            flash(f"An error occurred: {str(e)}")

    return render_template("index.html", result=result, encrypted_value=encrypted_value)


if __name__ == "__main__":
    app.run(port=5001, debug=True)
