from flask import Blueprint, request, jsonify, flash

submit = Blueprint('submit', __name__, template_folder='templates')


@submit.route('/submit', methods=['GET', 'POST'])
def submit_sigs():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        f = request.files['file']
        print(f, request.form['public_url'])
        return jsonify({}), 200
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=text name=public_url>
         <input type=submit value=Upload>
    </form>
    '''
