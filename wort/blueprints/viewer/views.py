import os

from flask import Blueprint, render_template, jsonify, redirect

viewer = Blueprint('viewer', __name__, template_folder='templates')


@viewer.route('/view/sra/<sra_id>')
def view_sra(sra_id):
    import boto3

    conn = boto3.client('s3')

    url = conn.generate_presigned_url(
            'get_object',
            Params = {
               'Bucket': "wort-sra",
               'Key': os.path.join('sigs', sra_id + '.sig'),
               'ResponseContentType': 'application/json',
#               'ResponseContentEncoding': 'gzip',
            },
            ExpiresIn=100)

    return redirect(url)
