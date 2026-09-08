from flask import Flask
from pyhive import hive
    
app = Flask(__name__)

@app.route('/patients_by_year')
def patients_by_year():
    # conn = hive.connect(host='192.168.56.101', port=10000, username='vagrant')
    # print(conn)
    # Ajoute ta logique SQL ici
    return {"message": "API is running, connect to Vagrant data here"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
