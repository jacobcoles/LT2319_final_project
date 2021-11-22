### Requirements
- Python 3.7+
- `pip install couchdb`


### Update the Visual Output Generator (VOG) database

1. You need to be logged into eduserv
`ssh -p 62266 -Y -L 16443:127.0.0.1:16443 gusXXXXXX@eduserv.flov.gu.se`

2. (In your local machine) Run the following command to forward the following port:
`kubectl port-forward svc/db-svc-couchdb 5984 -n gusXXXXXX &`

3. Run the Python script in this directory:
`python update_visual_output_db.py`