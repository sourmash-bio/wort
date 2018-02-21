import os

from flask import Blueprint, render_template, jsonify, redirect

viewer = Blueprint('viewer', __name__, template_folder='templates')


@viewer.route('/view/<db>/<dataset_id>')
def view_s3(db, dataset_id):

    if db not in ('sra', 'img'):
        return 404

    import boto3

    conn = boto3.client('s3')

    key = f'sigs/{dataset_id}.sig'
    # TODO: we don't really need this, I just copied the signatures improperly
    # to the bucket...
    if db == 'img':
        key = f'{dataset_id}.sig'

    url = conn.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': f"wort-{db}",
            'Key': key,
            'ResponseContentType': 'application/json',
            #'ResponseContentEncoding': 'gzip',
        },
        ExpiresIn=100)

    return redirect(url)
